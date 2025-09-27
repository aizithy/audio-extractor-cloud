# 集成指南：将增强功能集成到您的现有项目

本指南将帮助您将增强版视频音频提取功能集成到您现有的项目中。

## 🎯 集成选项

### 选项1：替换现有服务 (推荐)
使用增强版API完全替换现有的音频提取服务。

### 选项2：并行运行
同时运行增强版API和现有服务，逐步迁移功能。

### 选项3：功能集成
将增强版的关键功能集成到现有的`server/main.py`中。

## 🔄 选项1：完全替换 (推荐)

### 步骤1：备份现有项目
```bash
# 备份当前的server目录
cp -r /Users/enithz/Desktop/video/server /Users/enithz/Desktop/video/server_backup
```

### 步骤2：部署增强版服务
```bash
cd /Users/enithz/Desktop/video/enhanced_video_api

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 步骤3：更新iOS应用配置
修改iOS应用中的API端点地址：
```swift
// 在你的iOS应用中更新API基础URL
let baseURL = "http://localhost:8000"  // 或你的服务器地址

// 更新API调用
// 旧的API调用: POST /extract
// 新的API调用: POST /api/process
```

### 步骤4：API调用方式变更

#### 旧的API调用方式：
```swift
// 旧版本 - 同步处理
let request = ExtractRequest(url: videoURL, format: "m4a")
// 直接返回音频文件
```

#### 新的API调用方式：
```swift
// 新版本 - 异步任务处理
struct ProcessRequest: Codable {
    let url: String
    let extract_audio: Bool
    let keep_video: Bool
    let audio_format: String
    let audio_quality: String
}

// 1. 提交任务
let request = ProcessRequest(
    url: videoURL,
    extract_audio: true,
    keep_video: false,
    audio_format: "m4a",
    audio_quality: "good"
)

// 2. 查询状态直到完成
// 3. 下载文件
```

## 🔄 选项2：并行运行

### 配置不同端口
```bash
# 现有服务运行在8000端口
cd /Users/enithz/Desktop/video/server
python3 main.py  # 8000端口

# 增强版服务运行在8001端口
cd /Users/enithz/Desktop/video/enhanced_video_api
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### iOS应用中的逐步迁移
```swift
class AudioExtractionService {
    let legacyBaseURL = "http://localhost:8000"      // 旧版API
    let enhancedBaseURL = "http://localhost:8001"    // 增强版API
    
    func extractAudio(url: String, useEnhanced: Bool = false) {
        if useEnhanced {
            // 使用增强版API
            processWithEnhancedAPI(url: url)
        } else {
            // 使用旧版API
            processWithLegacyAPI(url: url)
        }
    }
}
```

## 🔄 选项3：功能集成

如果您希望保持现有的项目结构，可以将增强功能集成到现有的`server/main.py`中：

### 集成关键功能

#### 1. 添加任务管理系统
```python
# 在现有的server/main.py中添加
import uuid
from enum import Enum
from typing import Dict, Any

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 全局任务存储
tasks: Dict[str, Dict[str, Any]] = {}
```

#### 2. 增强yt-dlp配置
```python
def get_bilibili_enhanced_opts(output_path: str, extract_audio: bool = True):
    """B站专用增强配置"""
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': False,
        'extractor_args': {
            'bilibili': {
                'play_url_ssl': True,
                'api_preference': ['tv', 'web'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
        }
    }
    
    if extract_audio:
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '128',
        }]
    
    return opts
```

#### 3. 添加异步任务处理
```python
from fastapi import BackgroundTasks

@app.post("/api/process")
async def create_process_task(request: ExtractRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "progress": 0,
        "message": "任务已创建，正在处理中...",
        "created_at": time.time()
    }
    
    # 启动异步处理任务
    background_tasks.add_task(process_video_task, task_id, request)
    
    return {"task_id": task_id, "message": "任务已创建，正在处理中..."}

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks[task_id]
```

## 📱 iOS应用端集成

### 新的数据模型
```swift
// 新增数据模型
struct ProcessRequest: Codable {
    let url: String
    let extract_audio: Bool
    let keep_video: Bool
    let audio_format: String
    let audio_quality: String
}

struct ProcessResponse: Codable {
    let task_id: String
    let message: String
}

struct TaskStatusResponse: Codable {
    let status: String
    let progress: Int
    let message: String
    let video_title: String?
    let audio_file: String?
    let video_file: String?
    let duration: Int?
    let error_detail: String?
}
```

### 增强的音频提取服务
```swift
class EnhancedAudioExtractionService {
    private let baseURL: String
    
    init(baseURL: String = "http://localhost:8001") {
        self.baseURL = baseURL
    }
    
    func extractAudio(from url: String, 
                     format: String = "m4a",
                     quality: String = "good") async throws -> String {
        
        // 1. 提交任务
        let taskId = try await submitTask(url: url, format: format, quality: quality)
        
        // 2. 轮询状态直到完成
        let audioFile = try await waitForCompletion(taskId: taskId)
        
        // 3. 下载文件
        return try await downloadFile(filename: audioFile)
    }
    
    private func submitTask(url: String, format: String, quality: String) async throws -> String {
        let request = ProcessRequest(
            url: url,
            extract_audio: true,
            keep_video: false,
            audio_format: format,
            audio_quality: quality
        )
        
        let data = try JSONEncoder().encode(request)
        
        var urlRequest = URLRequest(url: URL(string: "\\(baseURL)/api/process")!)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = data
        
        let (responseData, _) = try await URLSession.shared.data(for: urlRequest)
        let response = try JSONDecoder().decode(ProcessResponse.self, from: responseData)
        
        return response.task_id
    }
    
    private func waitForCompletion(taskId: String, maxWaitTime: TimeInterval = 300) async throws -> String {
        let startTime = Date()
        
        while Date().timeIntervalSince(startTime) < maxWaitTime {
            let status = try await checkTaskStatus(taskId: taskId)
            
            switch status.status {
            case "completed":
                guard let audioFile = status.audio_file else {
                    throw ExtractionError.noAudioFile
                }
                return audioFile
                
            case "failed":
                throw ExtractionError.processingFailed(status.error_detail ?? "Unknown error")
                
            case "processing", "pending":
                // 继续等待
                try await Task.sleep(nanoseconds: 2_000_000_000) // 2秒
                
            default:
                throw ExtractionError.unknownStatus(status.status)
            }
        }
        
        throw ExtractionError.timeout
    }
    
    private func checkTaskStatus(taskId: String) async throws -> TaskStatusResponse {
        let url = URL(string: "\\(baseURL)/api/status/\\(taskId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(TaskStatusResponse.self, from: data)
    }
    
    private func downloadFile(filename: String) async throws -> String {
        let url = URL(string: "\\(baseURL)/api/download/\\(filename)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        
        // 保存到本地文件
        let documentsPath = FileManager.default.urls(for: .documentDirectory, 
                                                   in: .userDomainMask)[0]
        let localURL = documentsPath.appendingPathComponent(filename)
        
        try data.write(to: localURL)
        
        return localURL.path
    }
}

enum ExtractionError: Error {
    case noAudioFile
    case processingFailed(String)
    case unknownStatus(String)
    case timeout
}
```

### 在现有VideoStore中使用
```swift
// 在您的VideoStore.swift中集成
class VideoStore: ObservableObject {
    private let enhancedService = EnhancedAudioExtractionService()
    
    func extractAudioEnhanced(from url: String) async {
        do {
            let audioPath = try await enhancedService.extractAudio(from: url)
            
            DispatchQueue.main.async {
                // 更新UI，显示音频文件路径
                print("音频提取完成: \\(audioPath)")
            }
        } catch {
            DispatchQueue.main.async {
                print("音频提取失败: \\(error)")
            }
        }
    }
}
```

## 🧪 测试集成

### 测试现有功能兼容性
```bash
cd /Users/enithz/Desktop/video/enhanced_video_api
python3 test_enhanced_api.py
```

### 测试iOS应用集成
1. 启动增强版API服务
2. 在iOS模拟器中测试音频提取功能
3. 检查任务状态查询是否正常
4. 验证文件下载功能

## 🚀 部署建议

### 开发环境
- 本地运行增强版API服务
- iOS应用连接到`http://localhost:8001`

### 生产环境
- 部署增强版API到云服务器
- 更新iOS应用中的API端点地址
- 配置HTTPS和域名

## 📊 性能对比

| 功能 | 现有版本 | 增强版 |
|------|----------|--------|
| 处理方式 | 同步 | 异步 |
| 进度查询 | 无 | 实时 |
| 任务管理 | 无 | 完整 |
| 错误处理 | 基础 | 详细 |
| 平台优化 | 通用 | 专用 |
| 并发处理 | 限制 | 支持 |

## ⚠️ 注意事项

1. **数据兼容性**: 新旧API的数据格式不同，需要适配
2. **异步处理**: 需要修改iOS应用的同步调用为异步
3. **错误处理**: 增强版有更详细的错误信息
4. **性能**: 异步处理可能需要更长的响应时间
5. **存储**: 确保有足够的磁盘空间存储临时文件

## 🔧 故障排除

### 常见问题
1. **端口冲突**: 确保端口8001未被占用
2. **依赖缺失**: 检查虚拟环境和依赖安装
3. **FFmpeg**: 确保FFmpeg已正确安装
4. **网络**: 检查视频平台的网络连接

### 调试步骤
1. 检查API服务健康状态：`GET /api/health`
2. 查看控制台日志输出
3. 使用测试脚本验证功能
4. 检查临时文件目录权限

## 📞 获取支持

如果在集成过程中遇到问题：

1. 查看API文档：http://localhost:8001/docs
2. 运行测试脚本检查功能
3. 检查日志输出获取详细错误信息
4. 参考示例代码进行调试
