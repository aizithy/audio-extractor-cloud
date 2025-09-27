FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ffmpeg for yt-dlp postprocessing
ARG XRAY_VERSION=1.8.9
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl unzip ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    curl -L -o /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip && \
    unzip -q /tmp/xray.zip -d /tmp/xray && \
    mv /tmp/xray/xray /usr/bin/xray && chmod +x /usr/bin/xray && \
    rm -rf /tmp/xray /tmp/xray.zip

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

ENV PORT=8000 VT_TEMP_DIR=/tmp/video_transcriber
EXPOSE 8000
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
