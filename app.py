"""五线谱转简谱 web service.

Serves the jianpu renderer from ./static and exposes POST /api/omr, which runs
Audiveris on an uploaded score image or PDF and returns MusicXML.
"""
import asyncio
import os
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

AUDIVERIS = os.environ.get("AUDIVERIS_BIN", "/opt/audiveris/bin/Audiveris")
MAX_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "20")) * 1024 * 1024
TIMEOUT = int(os.environ.get("OMR_TIMEOUT", "300"))
ALLOWED = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

# Audiveris is memory hungry; run a limited number of jobs at once.
jobs = asyncio.Semaphore(int(os.environ.get("OMR_CONCURRENCY", "2")))
app = FastAPI(title="五线谱转简谱")


def read_mxl(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        name = None
        if "META-INF/container.xml" in z.namelist():
            root = ET.fromstring(z.read("META-INF/container.xml"))
            rf = next((e for e in root.iter() if e.tag.endswith("rootfile")), None)
            name = rf.get("full-path") if rf is not None else None
        if not name:
            name = next(n for n in z.namelist() if n.endswith((".xml", ".musicxml")) and not n.startswith("META-INF"))
        return z.read(name).decode("utf-8")


@app.post("/api/omr")
async def omr(file: UploadFile):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(415, "只支持 PDF 和 PNG、JPG、TIFF 图片。")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"文件超过 {MAX_BYTES // 1024 // 1024} MB，请压缩后再试。")

    work = Path(tempfile.mkdtemp(prefix="omr-"))
    try:
        src = work / f"score{ext}"
        src.write_bytes(data)
        out = work / "out"
        async with jobs:
            proc = await asyncio.create_subprocess_exec(
                AUDIVERIS, "-batch", "-export", "-output", str(out), "--", str(src),
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                await asyncio.wait_for(proc.wait(), TIMEOUT)
            except asyncio.TimeoutError:
                proc.kill()
                raise HTTPException(504, "识谱超时，请试试页数更少或更清晰的文件。")
        results = sorted(out.rglob("*.mxl")) + sorted(out.rglob("*.xml"))
        if not results:
            raise HTTPException(422, "没有识别出五线谱。请确认图片清晰、端正，并且是印刷乐谱。")
        xml = read_mxl(results[0]) if results[0].suffix == ".mxl" else results[0].read_text("utf-8")
        return Response(xml, media_type="application/vnd.recordare.musicxml+xml")
    finally:
        shutil.rmtree(work, ignore_errors=True)


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
