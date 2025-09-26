"""
增强版视频音频提取API服务
基于参考GitHub仓库：https://github.com/tmwgsicp/video-download-api
支持YouTube、Bilibili、TikTok等30+平台的视频下载和音频提取
"""

import os
import sys
import asyncio
import hashlib
import time
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum

# 设置UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yt_dlp
import uvicorn

# 配置 - 云端优化
PORT = int(os.environ.get("PORT", 8000))
TEMP_DIR = Path("/tmp/audio_extractor") if os.path.exists("/tmp") else Path("temp")
TEMP_DIR.mkdir(exist_ok=True)
MAX_FILE_AGE_HOURS = 1  # 云端环境更频繁清理

# 全局任务存储
tasks: Dict[str, Dict[str, Any]] = {}

app = FastAPI(
    title="增强版视频音频提取API",
    description="支持YouTube、Bilibili、TikTok等30+平台的视频下载和音频提取",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessRequest(BaseModel):
    """视频处理请求模型"""
    url: str = Field(..., description="视频URL")
    extract_audio: bool = Field(True, description="是否提取音频")
    keep_video: bool = Field(False, description="是否保留视频文件")
    audio_format: str = Field("mp3", description="音频格式: mp3, m4a, wav")
    audio_quality: str = Field("best", description="音频质量: best, good, normal")

class ProcessResponse(BaseModel):
    """处理响应模型"""
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")

class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(..., description="处理进度百分比")
    message: str = Field(..., description="状态消息")
    video_title: Optional[str] = Field(None, description="视频标题")
    video_file: Optional[str] = Field(None, description="视频文件名")
    audio_file: Optional[str] = Field(None, description="音频文件名")
    duration: Optional[int] = Field(None, description="时长(秒)")
    error_detail: Optional[str] = Field(None, description="错误详情")

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本")
    supported_sites: List[str] = Field(..., description="支持的网站")
    temp_files_count: int = Field(..., description="临时文件数量")

def get_supported_extractors():
    """获取支持的提取器列表"""
    try:
        # 创建临时yt-dlp实例来获取支持的提取器
        ydl = yt_dlp.YoutubeDL()
        extractors = list(ydl._get_available_extractors())
        
        # 常见平台
        common_sites = []
        priority_sites = [
            'youtube', 'bilibili', 'tiktok', 'twitter', 'instagram',
            'facebook', 'vimeo', 'dailymotion', 'twitch', 'xiaohongshu'
        ]
        
        for site in priority_sites:
            for extractor in extractors:
                if site.lower() in extractor.lower():
                    common_sites.append(extractor)
                    break
        
        return common_sites[:10]  # 返回前10个常见平台
    except:
        # 如果无法获取，返回默认列表
        return [
            "YouTube", "Bilibili", "TikTok", "Twitter", 
            "Instagram", "Facebook", "Vimeo", "Dailymotion"
        ]

def get_enhanced_ydl_opts(output_path: str, extract_audio: bool = True, 
                         audio_format: str = "mp3", quality: str = "best") -> Dict:
    """获取增强的yt-dlp配置选项"""
    
    # 音频质量映射
    audio_quality_map = {
        "best": "0",
        "good": "128",
        "normal": "96"
    }
    
    # 基础配置
    base_opts = {
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'retries': 3,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        # 平台特定配置
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'] if extract_audio else [],
                'player_client': ['android', 'web'],
            },
            'bilibili': {
                'play_url_ssl': True,
            }
        }
    }
    
    if extract_audio:
        # 仅音频模式
        base_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': audio_quality_map.get(quality, "128"),
            }],
        })
        
        if audio_format == "mp3":
            base_opts['postprocessor_args'] = {
                'ffmpeg': ['-ab', f'{audio_quality_map.get(quality, "128")}k']
            }
        elif audio_format == "m4a":
            base_opts['postprocessor_args'] = {
                'ffmpeg': ['-c:a', 'aac', '-b:a', f'{audio_quality_map.get(quality, "128")}k']
            }
    else:
        # 视频模式
        base_opts.update({
            'format': 'best[height<=720]/best',  # 限制最大分辨率
        })
    
    return base_opts

def get_bilibili_enhanced_opts(output_path: str, extract_audio: bool = True, 
                              audio_format: str = "mp3") -> Dict:
    """B站专用增强配置"""
    
    audio_quality_map = {"best": "0", "good": "128", "normal": "96"}
    
    opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best' if extract_audio else 'best[height<=720]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'retries': 3,
        'socket_timeout': 30,
        'extractor_args': {
            'bilibili': {
                'play_url_ssl': True,
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    }
    
    if extract_audio:
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': '128',
        }]
    
    return opts

def get_youtube_enhanced_opts(output_path: str, extract_audio: bool = True, 
                             audio_format: str = "mp3") -> Dict:
    """YouTube专用增强配置"""
    opts = get_enhanced_ydl_opts(output_path, extract_audio, audio_format)
    
    # YouTube特定优化
    opts.update({
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['android_creator', 'android', 'web'],
                'comment_sort': 'top',
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 11) gzip',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    })
    
    return opts

async def process_video_task(task_id: str, request: ProcessRequest):
    """异步处理视频任务"""
    try:
        # 更新任务状态
        tasks[task_id].update({
            "status": TaskStatus.PROCESSING,
            "progress": 10,
            "message": "开始分析视频信息..."
        })
        
        # 生成输出文件路径
        url_hash = hashlib.md5(request.url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_filename = f"{url_hash}_{timestamp}"
        video_path = str(TEMP_DIR / f"video_{base_filename}")
        audio_path = str(TEMP_DIR / f"audio_{base_filename}")
        
        # 检测平台并选择合适的配置
        platform_configs = {
            'bilibili.com': get_bilibili_enhanced_opts,
            'youtube.com': get_youtube_enhanced_opts,
            'youtu.be': get_youtube_enhanced_opts,
        }
        
        config_func = None
        for domain, func in platform_configs.items():
            if domain in request.url.lower():
                config_func = func
                break
        
        if not config_func:
            config_func = get_enhanced_ydl_opts
        
        # 更新进度
        tasks[task_id].update({
            "progress": 30,
            "message": "获取视频信息..."
        })
        
        # 获取视频信息
        info_opts = config_func("%(title)s", False)
        info_opts.update({'quiet': True, 'no_warnings': True})
        
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            if not info:
                raise Exception("无法获取视频信息")
            
            title = info.get('title', 'Unknown').encode('ascii', 'ignore').decode('ascii')
            duration = info.get('duration', 0)
            
            tasks[task_id].update({
                "video_title": title,
                "duration": duration,
                "progress": 50,
                "message": f"开始处理: {title[:50]}..."
            })
        
        # 处理音频
        audio_file = None
        if request.extract_audio:
            tasks[task_id].update({
                "progress": 60,
                "message": "提取音频中..."
            })
            
            audio_opts = config_func(
                audio_path, 
                extract_audio=True, 
                audio_format=request.audio_format
            )
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([request.url])
            
            # 查找生成的音频文件
            audio_files = list(TEMP_DIR.glob(f"audio_{base_filename}.*"))
            if audio_files:
                audio_file = audio_files[0].name
                tasks[task_id]["audio_file"] = audio_file
        
        # 处理视频
        video_file = None
        if request.keep_video:
            tasks[task_id].update({
                "progress": 80,
                "message": "下载视频中..."
            })
            
            video_opts = config_func(video_path, extract_audio=False)
            
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                ydl.download([request.url])
            
            # 查找生成的视频文件
            video_files = list(TEMP_DIR.glob(f"video_{base_filename}.*"))
            if video_files:
                video_file = video_files[0].name
                tasks[task_id]["video_file"] = video_file
        
        # 完成任务
        tasks[task_id].update({
            "status": TaskStatus.COMPLETED,
            "progress": 100,
            "message": "处理完成！",
            "audio_file": audio_file,
            "video_file": video_file
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"任务 {task_id} 处理失败: {error_msg}")
        
        tasks[task_id].update({
            "status": TaskStatus.FAILED,
            "progress": 0,
            "message": "处理失败",
            "error_detail": error_msg[:200]
        })

def cleanup_old_files():
    """清理过期文件"""
    try:
        current_time = time.time()
        for file_path in TEMP_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > MAX_FILE_AGE_HOURS * 3600:
                    try:
                        file_path.unlink()
                        print(f"已删除过期文件: {file_path.name}")
                    except Exception as e:
                        print(f"删除文件失败 {file_path.name}: {e}")
        
        # 清理过期任务
        expired_tasks = []
        for task_id, task_data in tasks.items():
            task_age = time.time() - task_data.get("created_at", 0)
            if task_age > MAX_FILE_AGE_HOURS * 3600:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del tasks[task_id]
            print(f"已删除过期任务: {task_id}")
            
    except Exception as e:
        print(f"清理过程中出错: {e}")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """API首页"""
    return {
        "service": "增强版视频音频提取API",
        "version": "1.0.0",
        "description": "支持YouTube、Bilibili、TikTok等30+平台",
        "endpoints": {
            "POST /api/process": "提交视频处理任务",
            "GET /api/status/{task_id}": "查询任务状态",
            "GET /api/download/{filename}": "下载文件",
            "GET /api/health": "健康检查"
        },
        "supported_features": [
            "多平台视频下载",
            "高质量音频提取", 
            "异步任务处理",
            "实时进度查询",
            "多种音频格式支持"
        ]
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check(background_tasks: BackgroundTasks):
    """健康检查"""
    background_tasks.add_task(cleanup_old_files)
    
    temp_files = list(TEMP_DIR.glob("*"))
    supported_sites = get_supported_extractors()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        supported_sites=supported_sites,
        temp_files_count=len(temp_files)
    )

@app.post("/api/process", response_model=ProcessResponse)
async def create_process_task(request: ProcessRequest, background_tasks: BackgroundTasks):
    """创建视频处理任务"""
    
    # 验证URL
    if not request.url or not request.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="无效的URL格式")
    
    # 检查是否支持抖音
    if 'douyin.com' in request.url.lower():
        raise HTTPException(
            status_code=400, 
            detail="抖音平台由于反爬限制暂时不支持，建议使用其他平台的视频"
        )
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "progress": 0,
        "message": "任务已创建，正在处理中...",
        "created_at": time.time(),
        "url": request.url,
        "extract_audio": request.extract_audio,
        "keep_video": request.keep_video
    }
    
    # 启动异步处理任务
    background_tasks.add_task(process_video_task, task_id, request)
    
    return ProcessResponse(
        task_id=task_id,
        message="任务已创建，正在处理中..."
    )

@app.get("/api/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_data = tasks[task_id]
    
    return TaskStatusResponse(
        status=task_data["status"],
        progress=task_data["progress"],
        message=task_data["message"],
        video_title=task_data.get("video_title"),
        video_file=task_data.get("video_file"),
        audio_file=task_data.get("audio_file"),
        duration=task_data.get("duration"),
        error_detail=task_data.get("error_detail")
    )

@app.get("/api/download/{filename}")
async def download_file(filename: str, background_tasks: BackgroundTasks):
    """下载文件"""
    background_tasks.add_task(cleanup_old_files)
    
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    
    # 根据文件扩展名确定媒体类型
    media_type_map = {
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska'
    }
    
    media_type = media_type_map.get(file_path.suffix.lower(), 'application/octet-stream')
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = Query(None, description="按状态过滤")):
    """列出所有任务"""
    if status:
        filtered_tasks = {
            tid: task for tid, task in tasks.items() 
            if task["status"] == status
        }
    else:
        filtered_tasks = tasks
    
    return {
        "total": len(filtered_tasks),
        "tasks": [
            {
                "task_id": tid,
                "status": task["status"],
                "progress": task["progress"],
                "message": task["message"],
                "created_at": datetime.fromtimestamp(task["created_at"]).isoformat()
            }
            for tid, task in filtered_tasks.items()
        ]
    }

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 删除相关文件
    task_data = tasks[task_id]
    for file_key in ["audio_file", "video_file"]:
        if file_key in task_data and task_data[file_key]:
            file_path = TEMP_DIR / task_data[file_key]
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
    
    # 删除任务记录
    del tasks[task_id]
    
    return {"message": "任务已删除"}

if __name__ == "__main__":
    # 启动时清理
    cleanup_old_files()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,  # 云端部署关闭自动重载
        log_level="info"
    )
