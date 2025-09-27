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

## Render 部署与 YouTube Cookies（解决需要登录/验证/风控）
部分 YouTube 链接在云端会提示“需要登录/验证码/像机器人”，可在 Render 设置环境变量 `YT_COOKIES_B64` 注入你的浏览器 cookies（Netscape 格式，Base64 编码）：

1) 从本机浏览器导出 cookies（Netscape 格式）。可用 `yt-dlp --cookies-from-browser chrome` 导出为 `cookies.txt`，或按项目 Wiki 导出。
2) 将 `cookies.txt` Base64 编码：
```bash
base64 -w0 cookies.txt > cookies.b64
```
macOS 可用：
```bash
base64 -i cookies.txt | tr -d '\n' > cookies.b64
```
3) 打开 Render → Environment → 添加变量：
   - `YT_COOKIES_B64` = 复制 `cookies.b64` 内容
   - 可选：`YT_CLIENTS=android,web`，`GEO_BYPASS_COUNTRY=US`，`YDL_PROXY=socks5h://user:pass@host:port`
4) 重新部署，日志中应看到 `cookiefile` 被启用（若失败会打印 `[cookies] load failed`）。

说明：我们不会保存 cookies 到仓库，仅运行时解码为 `/tmp/video_transcriber/yt_cookies.txt` 并传给 `yt-dlp`。
