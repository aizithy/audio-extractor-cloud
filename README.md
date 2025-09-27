# Audio Extractor Cloud (Zeabur Ready)

- FastAPI + yt-dlp 音频提取服务（支持 Bilibili/YouTube 等）
- 线程池下载，避免事件循环阻塞；异步任务 `/api/process` 支持进度与下载

## 本地运行
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 主要接口
- GET `/api/health`
- POST `/api/process` { url, extract_audio, audio_format, audio_quality }
- GET `/api/status/{task_id}`
- GET `/api/download/{filename}`
- POST `/extract` 兼容模式（直接流式返回）

## Docker 构建
```bash
docker build -t audio-extractor-cloud .
docker run -p 8000:8000 audio-extractor-cloud
```

## Zeabur 部署
- 新建服务 → Docker 项目 → 关联此仓库
- 环境变量：`PORT`（平台自动注入），`VT_TEMP_DIR=/tmp/video_transcriber`
- 入口：`uvicorn main:app --host 0.0.0.0 --port $PORT`
- 需要镜像包含 `ffmpeg`（Dockerfile 已内置）
