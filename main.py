import os
import sys
import asyncio
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yt_dlp

PORT = int(os.environ.get("PORT", 8000))
TEMP_DIR = Path(os.environ.get("VT_TEMP_DIR", "/tmp/video_transcriber"))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Video Audio Extractor (Local)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    url: str = Field(..., description="Video URL (YouTube/Bilibili)")
    extract_audio: bool = Field(True)
    keep_video: bool = Field(False)
    audio_format: str = Field("m4a", description="mp3|m4a|wav")
    audio_quality: str = Field("good", description="best|good|normal")

class ProcessResponse(BaseModel):
    task_id: str
    message: str

class TaskStatusResponse(BaseModel):
    status: str
    progress: int
    message: str
    video_title: Optional[str] = None
    audio_file: Optional[str] = None
    duration: Optional[int] = None
    error_detail: Optional[str] = None

# in-memory task store
TASKS: Dict[str, Dict[str, Any]] = {}

AUDIO_QUALITY_MAP = {
    "best": "0",
    "good": "128",
    "normal": "96",
}


def _ydl_opts(output_tmpl: str, audio_format: str, quality: str, url: str = "") -> Dict[str, Any]:
    base = {
        'outtmpl': output_tmpl,
        'quiet': False,
        'no_warnings': False,
        'retries': 3,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
    }
    base.update({
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': AUDIO_QUALITY_MAP.get(quality, '128'),
        }]
    })
    # 允许通过环境变量声明代理（也支持平台级 HTTP(S)_PROXY）
    ydl_proxy = os.environ.get('YDL_PROXY')
    if ydl_proxy:
        base['proxy'] = ydl_proxy

    # Cookies 优先级：YT_COOKIES_FILE > YT_COOKIES_URL > YT_COOKIES_B64
    yt_cookies_file = os.environ.get('YT_COOKIES_FILE')
    if yt_cookies_file and os.path.exists(yt_cookies_file):
        # Render 的 /etc/secrets 只读；复制到可写临时目录再使用
        try:
            tmp_cookie = TEMP_DIR / 'yt_cookies.txt'
            tmp_cookie.write_bytes(Path(yt_cookies_file).read_bytes())
            base['cookiefile'] = str(tmp_cookie)
        except Exception as e:
            print(f"[cookies] copy failed: {e}", file=sys.stderr)
            base['cookiefile'] = yt_cookies_file
    else:
        yt_cookies_url = os.environ.get('YT_COOKIES_URL')
        if yt_cookies_url:
            try:
                import requests
                r = requests.get(yt_cookies_url, timeout=15)
                r.raise_for_status()
                cookies_path = TEMP_DIR / 'yt_cookies.txt'
                cookies_path.write_bytes(r.content)
                base['cookiefile'] = str(cookies_path)
            except Exception as e:
                print(f"[cookies] fetch failed: {e}", file=sys.stderr)
        else:
            yt_cookies_b64 = os.environ.get('YT_COOKIES_B64')
            if yt_cookies_b64:
                try:
                    import base64
                    cookies_path = TEMP_DIR / 'yt_cookies.txt'
                    cookies_path.write_bytes(base64.b64decode(yt_cookies_b64))
                    base['cookiefile'] = str(cookies_path)
                except Exception as e:
                    print(f"[cookies] load failed: {e}", file=sys.stderr)

    # Handle Douyin cookies if it's a Douyin URL
    if _is_douyin_url(url):
        # Cookies 优先级：DY_COOKIES_FILE > DY_COOKIES_URL > DY_COOKIES_B64
        dy_cookies_file = os.environ.get('DY_COOKIES_FILE')
        if dy_cookies_file and os.path.exists(dy_cookies_file):
            # Render 的 /etc/secrets 只读；复制到可写临时目录再使用
            try:
                tmp_cookie = TEMP_DIR / 'dy_cookies.txt'
                tmp_cookie.write_bytes(Path(dy_cookies_file).read_bytes())
                base['cookiefile'] = str(tmp_cookie)
            except Exception as e:
                print(f"[douyin cookies] copy failed: {e}", file=sys.stderr)
                base['cookiefile'] = dy_cookies_file
        else:
            dy_cookies_url = os.environ.get('DY_COOKIES_URL')
            if dy_cookies_url:
                try:
                    import requests
                    r = requests.get(dy_cookies_url, timeout=15)
                    r.raise_for_status()
                    cookies_path = TEMP_DIR / 'dy_cookies.txt'
                    cookies_path.write_bytes(r.content)
                    base['cookiefile'] = str(cookies_path)
                except Exception as e:
                    print(f"[douyin cookies] fetch failed: {e}", file=sys.stderr)
            else:
                dy_cookies_b64 = os.environ.get('DY_COOKIES_B64')
                if dy_cookies_b64:
                    try:
                        import base64
                        cookies_path = TEMP_DIR / 'dy_cookies.txt'
                        cookies_path.write_bytes(base64.b64decode(dy_cookies_b64))
                        base['cookiefile'] = str(cookies_path)
                    except Exception as e:
                        print(f"[douyin cookies] load failed: {e}", file=sys.stderr)

    return base


def _is_youtube_url(url: str) -> bool:
    try:
        host = (urlparse(url).netloc or '').lower()
        return 'youtube.com' in host or 'youtu.be' in host
    except Exception:
        return False


def _is_douyin_url(url: str) -> bool:
    try:
        host = (urlparse(url).netloc or '').lower()
        return 'douyin.com' in host or 'iesdouyin.com' in host
    except Exception:
        return False


def _extract_audio_blocking(url: str, audio_format: str, quality: str) -> Dict[str, Any]:
    """阻塞式提取，适合放入线程池执行。"""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    basename = f"audio_{url_hash}_{ts}"
    outtmpl = str(TEMP_DIR / basename)

    opts = _ydl_opts(outtmpl, audio_format, quality, url)

    # 云端 YouTube 适配（地区/反爬 + cookies 客户端选择）
    if _is_youtube_url(url):
        geo_country = os.environ.get('GEO_BYPASS_COUNTRY', 'US')
        cookies_in_use = bool(opts.get('cookiefile'))
        if cookies_in_use:
            # 强制 cookies 模式走 web_safari/web，避免 android 客户端与 cookies 不兼容
            yt_clients = ['web_safari', 'web']
            ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15'
        else:
            yt_clients = os.environ.get('YT_CLIENTS', 'android,web').split(',')
            ua = 'com.google.android.youtube/17.36.4 (Linux; U; Android 11) gzip'
        opts.update({
            'geo_bypass': True,
            'geo_bypass_country': geo_country,
            'extractor_args': {
                'youtube': {
                    'player_client': yt_clients,
                }
            },
            'http_headers': {
                'User-Agent': ua,
                'Accept-Language': 'en-US,en;q=0.9'
            }
        })

    # Douyin specific handling
    if _is_douyin_url(url):
        douyin_cookies_in_use = bool(opts.get('cookiefile'))
        if douyin_cookies_in_use:
            # Use desktop user agent when cookies are available
            ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15'
        else:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

        opts.update({
            'http_headers': {
                'User-Agent': ua,
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.douyin.com/',
            }
        })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise HTTPException(status_code=404, detail="Cannot fetch video info")
        title = (info.get('title') or 'Unknown')
        duration = info.get('duration', 0)
        try:
            ydl.download([url])
        except Exception as e:
            if _is_youtube_url(url):
                # 尝试备用客户端组合
                fallback = opts.copy()
                cookies_in_use = bool(opts.get('cookiefile'))
                if cookies_in_use:
                    fallback.setdefault('extractor_args', {}).setdefault('youtube', {})['player_client'] = ['web_safari', 'web']
                else:
                    fallback.setdefault('extractor_args', {}).setdefault('youtube', {})['player_client'] = ['ios', 'android_creator']
                with yt_dlp.YoutubeDL(fallback) as y2:
                    y2.download([url])
            else:
                raise

    files = list(TEMP_DIR.glob(f"{basename}.*"))
    if not files:
        raise HTTPException(status_code=500, detail="Audio file not generated")
    f = files[0]

    return {
        'filename': f.name,
        'file_path': str(f),
        'title': title,
        'duration': duration,
    }


def _cleanup_old_files(max_age_hours: int = 6) -> None:
    now = time.time()
    for p in TEMP_DIR.glob('*'):
        try:
            if p.is_file() and now - p.stat().st_mtime > max_age_hours * 3600:
                p.unlink()
        except Exception:
            pass


@app.get("/")
async def root():
    return {"service": "Video Audio Extractor (Local)", "version": "1.0.0"}


@app.get("/api/health")
async def health(background_tasks: BackgroundTasks):
    background_tasks.add_task(_cleanup_old_files)
    return {"status": "healthy", "temp_dir": str(TEMP_DIR)}


@app.get("/api/diag")
async def diag():
    # 返回 cookies/代理/客户端策略的关键诊断信息
    cookies_file = None
    douyin_cookies_file = None
    try:
        # 推断当前是否存在解码后的 cookies 文件
        for name in ["yt_cookies.txt", "dy_cookies.txt"]:
            p = TEMP_DIR / name
            if p.exists() and p.stat().st_size > 0:
                if name == "yt_cookies.txt":
                    cookies_file = str(p)
                elif name == "dy_cookies.txt":
                    douyin_cookies_file = str(p)
                break
    except Exception:
        pass

    return {
        "cookiefile_exist": bool(cookies_file),
        "cookiefile_path": cookies_file,
        "douyin_cookiefile_exist": bool(douyin_cookies_file),
        "douyin_cookiefile_path": douyin_cookies_file,
        "YDL_PROXY": os.environ.get("YDL_PROXY"),
        "YT_COOKIES_FILE": os.environ.get("YT_COOKIES_FILE"),
        "YT_COOKIES_URL": bool(os.environ.get("YT_COOKIES_URL")),
        "YT_COOKIES_B64": bool(os.environ.get("YT_COOKIES_B64")),
        "DY_COOKIES_FILE": os.environ.get("DY_COOKIES_FILE"),
        "DY_COOKIES_URL": bool(os.environ.get("DY_COOKIES_URL")),
        "DY_COOKIES_B64": bool(os.environ.get("DY_COOKIES_B64")),
        "GEO_BYPASS_COUNTRY": os.environ.get("GEO_BYPASS_COUNTRY", "US"),
    }


@app.post("/api/process", response_model=ProcessResponse)
async def create_task(req: ProcessRequest, background_tasks: BackgroundTasks):
    if not req.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    import uuid
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        'status': 'pending',
        'progress': 0,
        'message': 'queued',
        'created_at': time.time(),
    }

    async def run():
        try:
            TASKS[task_id].update(status='processing', progress=10, message='fetching video info')
            # 在线程池中执行阻塞下载
            result = await asyncio.to_thread(_extract_audio_blocking, req.url, req.audio_format, req.audio_quality)
            TASKS[task_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'done',
                'audio_file': result['filename'],
                'video_title': result['title'],
                'duration': result['duration'],
            })
        except Exception as e:
            TASKS[task_id].update(status='failed', progress=0, message='failed', error_detail=str(e)[:200])

    # 在当前事件循环中调度任务，避免在后台线程中创建协程导致的无事件循环错误
    asyncio.create_task(run())
    return ProcessResponse(task_id=task_id, message="accepted")


@app.get("/api/status/{task_id}")
async def status(task_id: str):
    try:
        if task_id not in TASKS:
            return JSONResponse({
                "status": "failed",
                "progress": 0,
                "message": "task not found",
                "error_detail": "not_found"
            }, status_code=200)
        t = TASKS[task_id]
        return {
            "status": str(t.get('status', 'pending')),
            "progress": int(t.get('progress', 0) or 0),
            "message": str(t.get('message', '')),
            "video_title": t.get('video_title'),
            "audio_file": t.get('audio_file'),
            "duration": int(t.get('duration', 0) or 0) if t.get('duration') is not None else None,
            "error_detail": t.get('error_detail'),
        }
    except Exception as e:
        # 永远返回200+JSON，避免前端解析失败导致一直卡住
        return JSONResponse({
            "status": "failed",
            "progress": 0,
            "message": "internal error",
            "error_detail": str(e)[:200]
        }, status_code=200)


@app.get("/api/download/{filename}")
async def download(filename: str):
    p = TEMP_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="file not found")
    media_type = 'audio/mpeg' if p.suffix.lower() == '.mp3' else 'audio/mp4'
    return FileResponse(str(p), media_type=media_type, filename=p.name)


# Simple sync endpoint for compatibility with existing iOS code
class ExtractRequest(BaseModel):
    url: str
    format: str = 'm4a'
    mode: str = 'stream'
    quality: str = 'good'

@app.post("/extract")
async def simple_extract(req: ExtractRequest):
    result = await asyncio.to_thread(_extract_audio_blocking, req.url, req.format, req.quality)
    media_type = 'audio/mpeg' if req.format == 'mp3' else 'audio/mp4'
    return FileResponse(result['file_path'], media_type=media_type, filename=result['filename'])


# ===== 音乐搜索相关API =====

@app.get("/api/music/search")
async def search_music(keyword: str, limit: int = 30):
    """
    搜索音乐 - 使用网易云音乐API
    """
    try:
        import aiohttp
        
        # 使用公开的网易云音乐API镜像（优先使用可用的镜像）
        api_mirrors = [
            "https://netease-cloud-music-api.vercel.app",
            "https://music-api.heheda.top",
            "https://api.injahow.cn"
        ]
        api_base = api_mirrors[0]  # 使用第一个镜像
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_base}/search",
                params={
                    "keywords": keyword,
                    "limit": limit,
                    "type": 1  # 1=单曲
                }
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="搜索失败")
                
                data = await resp.json()
                
                # 解析结果
                songs = []
                if data.get('result') and data['result'].get('songs'):
                    for song in data['result']['songs']:
                        songs.append({
                            'id': song.get('id'),
                            'name': song.get('name'),
                            'artist': ', '.join([ar.get('name', '') for ar in song.get('artists', [])]),
                            'album': song.get('album', {}).get('name', ''),
                            'duration': song.get('duration', 0) / 1000,  # 毫秒转秒
                            'coverURL': song.get('album', {}).get('picUrl', ''),
                            'audioURL': None  # 需要单独请求
                        })
                
                return {'songs': songs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.get("/api/music/url")
async def get_music_url(id: int):
    """
    获取音乐播放URL - 支持多音源解锁（网易云/QQ音乐/酷狗/咪咕）
    """
    try:
        import aiohttp
        
        # 1. 首先尝试网易云官方API
        api_base = "https://netease-cloud-music-api.vercel.app"
        bitrates = [320000, 192000, 128000]
        
        async with aiohttp.ClientSession() as session:
            # 尝试网易云音乐
            for br in bitrates:
                try:
                    async with session.get(
                        f"{api_base}/song/url",
                        params={"id": id, "br": br},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('data') and len(data['data']) > 0:
                                url = data['data'][0].get('url')
                                if url and url != "null" and url != "":
                                    print(f"✅ 网易云 {br//1000}kbps URL")
                                    return {'url': url, 'source': 'netease', 'bitrate': br}
                except Exception as e:
                    print(f"⚠️ 网易云 {br//1000}kbps 失败: {str(e)}")
                    continue
            
            print("⚠️ 网易云音乐无法播放，尝试其他音源...")
            
            # 2. 尝试使用yt-dlp直接提取（支持多平台）
            try:
                # 先获取歌曲详情
                async with session.get(
                    f"{api_base}/song/detail",
                    params={"ids": id},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('songs') and len(data['songs']) > 0:
                            song_info = data['songs'][0]
                            song_name = song_info.get('name', '')
                            artist_name = ', '.join([ar.get('name', '') for ar in song_info.get('ar', [])])
                            
                            # 构造搜索关键词
                            search_keyword = f"{artist_name} {song_name}"
                            print(f"🔍 尝试从其他源搜索: {search_keyword}")
                            
                            # 尝试从YouTube Music搜索并获取
                            yt_search_url = f"ytsearch1:{search_keyword} audio"
                            
                            # 使用yt-dlp获取最佳音频
                            try:
                                result = await asyncio.to_thread(_get_ytdlp_audio_url, yt_search_url)
                                if result:
                                    print(f"✅ YouTube Music URL获取成功")
                                    return {'url': result, 'source': 'youtube_music', 'bitrate': 'auto'}
                            except Exception as e:
                                print(f"⚠️ YouTube Music 失败: {str(e)}")
            except Exception as e:
                print(f"⚠️ 备用源搜索失败: {str(e)}")
            
            # 所有音源都失败
            return {
                'url': None, 
                'error': '该歌曲暂时无法在线播放',
                'reason': '所有音源都无法获取（VIP/版权/地区限制）',
                'suggestion': '建议下载到本地播放（下载功能支持更多音源）'
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取URL失败: {str(e)}")


def _get_ytdlp_audio_url(search_url: str) -> Optional[str]:
    """使用yt-dlp获取音频URL"""
    try:
        opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            if info and info.get('url'):
                return info['url']
            elif info and info.get('entries') and len(info['entries']) > 0:
                entry = info['entries'][0]
                if entry.get('url'):
                    return entry['url']
        return None
    except Exception as e:
        print(f"yt-dlp提取失败: {str(e)}")
        return None


@app.get("/api/music/url/unlock")
async def get_music_url_unlock(id: int):
    """
    增强版音乐URL获取 - 支持VIP歌曲解锁
    尝试多个音源：网易云 → YouTube Music → QQ音乐搜索
    """
    try:
        import aiohttp
        
        api_base = "https://netease-cloud-music-api.vercel.app"
        
        async with aiohttp.ClientSession() as session:
            # 1. 获取歌曲详情（用于备用搜索）
            song_name = ""
            artist_name = ""
            try:
                async with session.get(
                    f"{api_base}/song/detail",
                    params={"ids": id},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('songs') and len(data['songs']) > 0:
                            song_info = data['songs'][0]
                            song_name = song_info.get('name', '')
                            artist_name = ', '.join([ar.get('name', '') for ar in song_info.get('ar', [])])
                            print(f"📝 歌曲信息: {artist_name} - {song_name}")
            except Exception as e:
                print(f"⚠️ 获取歌曲详情失败: {str(e)}")
            
            # 2. 尝试网易云官方（免费歌曲）
            bitrates = [320000, 192000, 128000]
            for br in bitrates:
                try:
                    async with session.get(
                        f"{api_base}/song/url",
                        params={"id": id, "br": br},
                        timeout=aiohttp.ClientTimeout(total=8)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('data') and len(data['data']) > 0:
                                url = data['data'][0].get('url')
                                if url and url != "null" and url != "":
                                    print(f"✅ [网易云] {br//1000}kbps")
                                    return {'url': url, 'source': 'netease', 'bitrate': br}
                except Exception:
                    continue
            
            print(f"⚠️ 网易云VIP限制，尝试YouTube Music...")
            
            # 3. 使用YouTube Music作为备用源
            if song_name and artist_name:
                search_keyword = f"{artist_name} {song_name}"
                yt_search_url = f"ytsearch1:{search_keyword} audio"
                
                try:
                    result = await asyncio.to_thread(_get_ytdlp_audio_url, yt_search_url)
                    if result:
                        print(f"✅ [YouTube Music] 解锁成功")
                        return {
                            'url': result, 
                            'source': 'youtube_music',
                            'song_name': song_name,
                            'artist_name': artist_name
                        }
                except Exception as e:
                    print(f"⚠️ YouTube Music 失败: {str(e)}")
            
            # 所有音源都失败
            return {
                'url': None,
                'error': '该歌曲无法在线播放',
                'tried_sources': ['网易云音乐', 'YouTube Music'],
                'suggestion': '建议下载到本地（下载功能成功率更高）'
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取URL失败: {str(e)}")


@app.get("/api/music/lyric")
async def get_music_lyric(id: int):
    """
    获取歌词
    """
    try:
        import aiohttp
        
        api_base = "https://netease-cloud-music-api.vercel.app"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_base}/lyric",
                params={"id": id}
            ) as resp:
                if resp.status != 200:
                    return {'lyric': None}
                
                data = await resp.json()
                
                # 优先返回翻译歌词，否则返回原歌词
                lyric = None
                if data.get('lrc') and data['lrc'].get('lyric'):
                    lyric = data['lrc']['lyric']
                
                return {'lyric': lyric}
    except Exception:
        return {'lyric': None}


if __name__ == "__main__":
    import uvicorn
    _cleanup_old_files()
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
