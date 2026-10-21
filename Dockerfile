FROM --platform=linux/amd64 ubuntu:24.04

ARG AUDIVERIS_VERSION=5.9.0
ENV DEBIAN_FRONTEND=noninteractive
# Audiveris reads lyrics and titles with Tesseract in legacy mode, which needs the
# full traineddata files (Ubuntu's packages ship the LSTM-only ones).
ENV TESSDATA_PREFIX=/opt/tessdata

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl python3 python3-venv \
      fontconfig fonts-dejavu-core \
 && curl -fsSL -o /tmp/audiveris.deb \
      "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb" \
 && mkdir -p /usr/share/desktop-directories /usr/share/applications /usr/share/mime/packages \
 && apt-get install -y --no-install-recommends /tmp/audiveris.deb \
 && mkdir -p /opt/tessdata \
 && for l in eng chi_sim; do \
      curl -fsSL -o /opt/tessdata/$l.traineddata "https://github.com/tesseract-ocr/tessdata/raw/main/$l.traineddata"; \
    done \
 && rm -rf /tmp/audiveris.deb /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY static ./static

EXPOSE 8000
CMD ["/venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
