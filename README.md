# 五线谱转简谱

上传五线谱图片、PDF 或 MusicXML，在网页里按首调生成简谱。

- 前端：`static/index.html`，单个页面，负责解析 MusicXML 并用 SVG 画出简谱（首调 1=X、高低八度点、减时线、增时线、附点、连音线、三连音、歌词、多声部切换）。
- 后端：`app.py`（FastAPI），`POST /api/omr` 接收图片或 PDF，调用 [Audiveris](https://github.com/Audiveris/audiveris) 识谱，返回 MusicXML。

## 用 Docker 运行

```bash
docker build -t jianpu .
docker run -p 8000:8000 jianpu
```

然后打开 http://localhost:8000 。容器建议至少 2 GB 内存。

## 本地开发

需要 Python 3.10+，并单独安装 Audiveris（https://github.com/Audiveris/audiveris/releases）。

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
AUDIVERIS_BIN=/opt/audiveris/bin/Audiveris .venv/bin/uvicorn app:app --reload
```

环境变量：`AUDIVERIS_BIN`、`MAX_UPLOAD_MB`（默认 20）、`OMR_TIMEOUT`（秒，默认 300）、`OMR_CONCURRENCY`（默认 2）。

## 识谱效果

印刷清晰、拍摄端正的乐谱效果最好，手写谱基本识别不了。测试中，一张倾斜、带噪点的《欢乐颂》照片 62 个音全部识别正确，约 6 秒。

## 许可证说明

Audiveris 使用 AGPL-3.0 许可证。本项目把它作为独立程序调用；如果修改了 Audiveris 本身并公开提供服务，需要按 AGPL 公开修改后的源码。
