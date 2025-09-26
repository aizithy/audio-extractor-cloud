# 🚀 增强版视频音频提取API - 云端部署版

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates)

> 基于参考项目 [video-download-api](https://github.com/tmwgsicp/video-download-api) 构建的增强版云端服务

## ✨ 主要特性

### 🌍 多平台支持
- **Bilibili** - 优化的B站视频音频提取
- **YouTube** - 智能多客户端策略
- **TikTok** - 国际版短视频平台
- **Twitter/X** - 社交媒体视频
- **Instagram** - 图片和视频内容
- **30+其他平台** - 基于yt-dlp的广泛支持

### 🎵 强大的音频处理
- **多格式支持**: MP3、M4A、WAV
- **音质选择**: 最佳、良好、普通
- **智能提取**: 平台专用优化配置
- **批量处理**: 异步任务队列

### 🔥 云端优势
- **零配置部署**: 一键部署到Zeabur
- **自动扩展**: 根据负载自动调整
- **全球CDN**: 快速访问速度
- **免费额度**: 支持个人和小团队使用

## 🚀 快速部署

### 方法1：一键部署到Zeabur
1. 点击上方的 "Deploy on Zeabur" 按钮
2. 授权GitHub并选择此仓库
3. 等待自动部署完成
4. 获取部署URL并开始使用

### 方法2：手动部署到Zeabur
1. Fork此仓库到您的GitHub账户
2. 在Zeabur控制台创建新项目
3. 选择GitHub仓库并连接
4. Zeabur会自动识别配置并部署

### 方法3：Docker部署
```bash
# 构建镜像
docker build -t enhanced-video-api .

# 运行容器
docker run -p 8000:8000 enhanced-video-api
```

## 📖 API使用指南

### 基础信息
- **API基础URL**: `https://your-deployment-url.zeabur.app`
- **API文档**: `https://your-deployment-url.zeabur.app/docs`
- **健康检查**: `https://your-deployment-url.zeabur.app/api/health`

### 核心API接口

#### 1. 异步音频提取 (推荐)
```bash
# 提交任务
curl -X POST "https://your-domain.zeabur.app/api/process" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.bilibili.com/video/BV1xx411c7mD",
       "extract_audio": true,
       "keep_video": false,
       "audio_format": "mp3",
       "audio_quality": "good"
     }'

# 查询状态
curl "https://your-domain.zeabur.app/api/status/{task_id}"

# 下载文件
curl -O "https://your-domain.zeabur.app/api/download/{filename}"
```

#### 2. 兼容模式 (同步)
```bash
curl -X POST "https://your-domain.zeabur.app/extract" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.bilibili.com/video/BV1xx411c7mD",
       "format": "m4a",
       "mode": "stream",
       "quality": "good"
     }'
```

### 🎯 使用示例

#### JavaScript/Web应用
```javascript
class VideoAudioAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async extractAudio(videoURL, options = {}) {
    // 1. 提交任务
    const response = await fetch(`${this.baseURL}/api/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: videoURL,
        extract_audio: true,
        keep_video: false,
        audio_format: options.format || 'mp3',
        audio_quality: options.quality || 'good'
      })
    });
    
    const { task_id } = await response.json();
    
    // 2. 轮询状态
    return this.waitForCompletion(task_id);
  }

  async waitForCompletion(taskId) {
    while (true) {
      const response = await fetch(`${this.baseURL}/api/status/${taskId}`);
      const status = await response.json();
      
      if (status.status === 'completed') {
        return `${this.baseURL}/api/download/${status.audio_file}`;
      } else if (status.status === 'failed') {
        throw new Error(status.error_detail);
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

// 使用示例
const api = new VideoAudioAPI('https://your-domain.zeabur.app');
api.extractAudio('https://www.bilibili.com/video/BV1xx411c7mD')
   .then(downloadURL => console.log('下载链接:', downloadURL))
   .catch(error => console.error('提取失败:', error));
```

#### Python应用
```python
import requests
import time

class VideoAudioAPI:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def extract_audio(self, video_url, audio_format='mp3', quality='good'):
        # 提交任务
        response = requests.post(f"{self.base_url}/api/process", json={
            "url": video_url,
            "extract_audio": True,
            "keep_video": False,
            "audio_format": audio_format,
            "audio_quality": quality
        })
        
        task_id = response.json()["task_id"]
        
        # 等待完成
        while True:
            status_response = requests.get(f"{self.base_url}/api/status/{task_id}")
            status = status_response.json()
            
            if status["status"] == "completed":
                return f"{self.base_url}/api/download/{status['audio_file']}"
            elif status["status"] == "failed":
                raise Exception(status.get("error_detail", "Unknown error"))
            
            time.sleep(2)

# 使用示例
api = VideoAudioAPI('https://your-domain.zeabur.app')
download_url = api.extract_audio('https://www.bilibili.com/video/BV1xx411c7mD')
print(f"下载链接: {download_url}")
```

## 🌍 支持的平台

### ✅ 完全支持
| 平台 | 状态 | 特殊优化 |
|------|------|----------|
| Bilibili | ✅ | 专用API配置 |
| YouTube | ✅ | 多客户端策略 |
| TikTok | ✅ | 国际版支持 |
| Twitter/X | ✅ | 社交媒体优化 |
| Instagram | ✅ | 视频内容提取 |
| 小红书 | ✅ | 生活分享平台 |
| Facebook | ✅ | 社交视频 |
| Vimeo | ✅ | 专业视频 |

### ❌ 限制说明
- **抖音(Douyin)**: 反爬限制严格，暂不支持
- **私有视频**: 需要登录的内容可能失败
- **版权保护**: 部分受保护内容无法提取

## 📊 性能说明

### 处理能力
- **短视频** (1-5分钟): 通常30秒-2分钟
- **中等视频** (5-30分钟): 通常2-10分钟
- **长视频** (30分钟+): 根据视频大小和网络状况

### 资源限制
- **文件大小**: 建议50MB以内的音频文件
- **处理时间**: 最长30分钟超时
- **并发数**: 支持多任务并行处理
- **存储**: 文件自动清理，保留1小时

## 🔧 高级配置

### 环境变量
```bash
PORT=8000                    # 服务端口
MAX_FILE_AGE_HOURS=1        # 文件保留时间
PYTHONIOENCODING=utf-8      # 编码设置
```

### 自定义部署
如需自定义部署配置，可以修改以下文件：
- `zeabur.json`: Zeabur部署配置
- `Dockerfile`: Docker容器配置
- `requirements.txt`: Python依赖

## 🛠️ 开发和贡献

### 本地开发
```bash
# 克隆仓库
git clone https://github.com/your-username/enhanced-video-audio-api.git
cd enhanced-video-audio-api

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python3 start.py
```

### 测试
```bash
# 运行测试
python3 test_enhanced_api.py

# 测试特定URL
python3 test_enhanced_api.py "https://www.bilibili.com/video/BV1xx411c7mD"
```

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- **原项目灵感**: [video-download-api](https://github.com/tmwgsicp/video-download-api)
- **核心依赖**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- **Web框架**: [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- **媒体处理**: [FFmpeg](https://ffmpeg.org/) - 多媒体处理工具包

## 📞 支持

- **问题报告**: 在GitHub Issues中提交
- **功能请求**: 在GitHub Discussions中讨论
- **文档**: 访问部署后的 `/docs` 端点查看完整API文档

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**
