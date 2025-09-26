# 🚀 增强版视频音频提取API - 云端部署版

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates)

> 基于参考项目 [video-download-api](https://github.com/tmwgsicp/video-download-api) 构建的增强版云端服务，支持YouTube、Bilibili、TikTok等30+平台的视频下载和音频提取。

## ✨ 主要特性

### 🌍 多平台支持
- **YouTube** - 全球最大视频平台
- **Bilibili** - 中国知名视频网站  
- **TikTok** - 短视频平台
- **Twitter/X** - 社交媒体视频
- **Instagram** - 图片和视频社交
- **小红书** - 生活方式分享平台
- **其他30+平台** - 详见yt-dlp支持列表

### 🎵 音频提取功能
- **多种格式**: MP3、M4A、WAV
- **音质选择**: 最佳、良好、普通
- **智能优化**: 针对不同平台的专用配置
- **批量处理**: 支持多个视频同时处理

### 🚀 API特性
- **异步处理**: 任务提交后立即返回，支持进度查询
- **RESTful设计**: 标准的REST API接口
- **实时状态**: 实时查询处理进度和状态
- **错误处理**: 详细的错误信息和处理建议
- **自动清理**: 自动清理过期的临时文件

### 📊 任务管理
- **任务队列**: 异步任务处理队列
- **进度追踪**: 实时进度更新
- **状态管理**: 待处理、处理中、已完成、失败
- **任务查询**: 支持按状态过滤查询

## 🛠️ 技术架构

### 核心技术栈
- **FastAPI** - 现代化的Python Web框架
- **yt-dlp** - 视频下载和处理，支持1000+网站
- **FFmpeg** - 音视频处理工具
- **Pydantic** - 数据验证和序列化
- **asyncio** - 异步编程支持

### 平台优化策略
- **Bilibili专用配置**: 优化的API选择和请求头
- **YouTube增强**: 多客户端策略和反检测机制
- **通用优化**: 智能重试和错误恢复

## 🚀 快速开始

### 环境要求
- Python 3.8+
- FFmpeg (必须)
- 8GB+ 可用磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone <this-repo>
cd enhanced_video_api
```

2. **一键启动**
```bash
python start.py
```

启动脚本会自动：
- 检查Python版本
- 检查FFmpeg安装
- 安装Python依赖
- 创建必要目录
- 启动API服务

### 手动安装
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问服务
- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

## 📖 API使用指南

### 基本流程
1. **提交任务** → 2. **查询状态** → 3. **下载文件**

### API接口

#### 1. 健康检查
```http
GET /api/health
```

响应：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "supported_sites": ["YouTube", "Bilibili", "TikTok", ...],
  "temp_files_count": 5
}
```

#### 2. 提交视频处理任务
```http
POST /api/process
Content-Type: application/json

{
  "url": "https://www.bilibili.com/video/BV1xx411c7mD",
  "extract_audio": true,
  "keep_video": false,
  "audio_format": "mp3",
  "audio_quality": "good"
}
```

响应：
```json
{
  "task_id": "uuid-string",
  "message": "任务已创建，正在处理中..."
}
```

#### 3. 查询任务状态
```http
GET /api/status/{task_id}
```

响应：
```json
{
  "status": "completed",
  "progress": 100,
  "message": "处理完成！",
  "video_title": "视频标题",
  "video_file": "video_abc123.mp4",
  "audio_file": "audio_abc123.mp3",
  "duration": 180
}
```

#### 4. 下载文件
```http
GET /api/download/{filename}
```

#### 5. 任务管理
```http
GET /api/tasks                    # 列出所有任务
GET /api/tasks?status=completed   # 按状态过滤
DELETE /api/tasks/{task_id}       # 删除任务
```

### 使用示例

#### 🎵 仅提取音频 (MP3)
```bash
curl -X POST "http://localhost:8000/api/process" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.bilibili.com/video/BV1xx411c7mD",
       "extract_audio": true,
       "keep_video": false,
       "audio_format": "mp3",
       "audio_quality": "good"
     }'
```

#### 🎬 同时下载视频和音频
```bash
curl -X POST "http://localhost:8000/api/process" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.bilibili.com/video/BV1xx411c7mD",
       "extract_audio": true,
       "keep_video": true,
       "audio_format": "m4a",
       "audio_quality": "best"
     }'
```

#### 📹 仅下载视频
```bash
curl -X POST "http://localhost:8000/api/process" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.bilibili.com/video/BV1xx411c7mD",
       "extract_audio": false,
       "keep_video": true
     }'
```

## 🧪 测试

### 运行测试脚本
```bash
# 全面测试
python test_enhanced_api.py

# 测试单个URL
python test_enhanced_api.py "https://www.bilibili.com/video/BV1xx411c7mD"
```

### 测试功能
- **健康检查测试**
- **多平台测试** (Bilibili、YouTube等)
- **音频格式测试** (MP3、M4A等)
- **错误处理测试**

## 🌍 支持平台

### ✅ 完全支持
- **YouTube** - 采用多客户端策略
- **Bilibili** - 优化的API配置
- **TikTok** - 国际版
- **Twitter/X** - 社交媒体视频
- **Instagram** - 视频内容
- **小红书** - 生活分享
- **更多平台** - 基于yt-dlp的1000+网站

### ❌ 限制说明
- **抖音(Douyin)** - 反爬限制严格，暂不支持
- **部分私有视频** - 需要登录的内容可能失败
- **年龄限制视频** - 可能需要特殊处理

## 📈 性能与限制

### 处理能力
- **短视频** (1-5分钟): 30秒-2分钟
- **中等视频** (5-30分钟): 2-10分钟  
- **长视频** (30分钟+): 云端版本限制1小时

### 资源使用
- **内存**: 200MB-1GB (处理过程中)
- **磁盘**: 自动清理临时文件
- **网络**: 取决于视频大小和质量

### 并发处理
- 支持多任务并发
- 异步任务队列
- 自动负载均衡

## 🔧 配置选项

### 音频质量
- **best**: 最高质量 (192kbps+)
- **good**: 良好质量 (128kbps)
- **normal**: 普通质量 (96kbps)

### 音频格式
- **MP3**: 通用兼容性最好
- **M4A**: 质量较好，支持AAC编码
- **WAV**: 无损格式，文件较大

### 平台特定设置
每个平台都有优化的配置：
- 请求头优化
- API端点选择
- 重试策略
- 错误处理

## 🔒 安全考虑

- **输入验证**: 严格的URL格式检查
- **文件安全**: 自动清理临时文件
- **错误处理**: 防止敏感信息泄露
- **资源限制**: 防止资源滥用

## 🤝 与原项目的差异

基于 [video-download-api](https://github.com/tmwgsicp/video-download-api) 进行了以下增强：

### 🆕 新增功能
- **异步任务处理**: 非阻塞的任务队列
- **实时进度查询**: 详细的处理状态
- **任务管理**: 完整的CRUD操作
- **平台优化**: 针对不同平台的专用配置
- **错误恢复**: 智能重试和错误处理

### 🔧 技术改进
- **更好的错误处理**: 详细的错误分类和建议
- **性能优化**: 异步处理和资源管理
- **代码结构**: 模块化和可维护性
- **文档完善**: 详细的API文档和使用指南

## 📞 技术支持

### 常见问题
1. **FFmpeg未安装**: 请按照安装指南安装FFmpeg
2. **YouTube限制**: 尝试不同的视频或稍后重试
3. **B站限制**: 某些高质量视频可能需要登录
4. **网络超时**: 检查网络连接或使用VPN

### 获取帮助
- 查看API文档: http://localhost:8000/docs
- 运行健康检查: http://localhost:8000/api/health
- 查看日志输出以获取详细错误信息

## 📄 许可证

本项目采用与原项目相同的 Apache 2.0 许可证。

## 🙏 致谢

- **原项目**: [video-download-api](https://github.com/tmwgsicp/video-download-api)
- **yt-dlp**: 强大的视频下载工具
- **FastAPI**: 现代化的Python Web框架
- **FFmpeg**: 多媒体处理工具包
