# 🚀 Render 部署指南 - 音乐搜索增强版

## ✅ GitHub 推送完成

**仓库地址**: https://github.com/aizithy/audio-extractor-cloud

**最新提交**: 
```
10e39e8 feat: 添加在线音乐搜索API功能
- 新增 /api/music/search 端点
- 新增 /api/music/url 端点  
- 新增 /api/music/lyric 端点
- 添加 aiohttp 依赖
```

---

## 📋 Render 自动部署配置

### 步骤1：创建新的Web Service

1. **登录 Render**: https://dashboard.render.com/

2. **创建新服务**:
   - 点击 "New +" → "Web Service"

3. **连接 GitHub 仓库**:
   - 选择 "Connect a repository"
   - 授权 Render 访问您的 GitHub（如果还没有）
   - 选择仓库: `aizithy/audio-extractor-cloud`

### 步骤2：配置服务设置

#### 基本设置
```
Name: audio-extractor-api
Region: Oregon (US West) 或最近的区域
Branch: main
```

#### 构建设置
```
Root Directory: (留空)
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 步骤3：环境变量配置

**必需的环境变量**:

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `PORT` | (自动) | Render自动注入 |
| `VT_TEMP_DIR` | `/tmp/video_transcriber` | 临时文件目录 |
| `PYTHON_VERSION` | `3.11.0` | Python版本 |

**可选的环境变量**（用于解决YouTube/抖音限制）:

| 变量名 | 说明 |
|--------|------|
| `YT_COOKIES_FILE` | YouTube cookies文件路径 |
| `YT_COOKIES_URL` | YouTube cookies下载URL |
| `YT_COOKIES_B64` | YouTube cookies Base64编码 |
| `DY_COOKIES_FILE` | 抖音cookies文件路径 |
| `DY_COOKIES_URL` | 抖音cookies下载URL |
| `DY_COOKIES_B64` | 抖音cookies Base64编码 |
| `YDL_PROXY` | 代理设置 (如: `socks5h://user:pass@host:port`) |
| `GEO_BYPASS_COUNTRY` | 地理位置绕过 (默认: `US`) |
| `YT_CLIENTS` | YouTube客户端 (默认: `android,web`) |

### 步骤4：选择服务计划

**推荐配置**:
- **Free Tier** (开发/测试)
  - 0 USD/月
  - 750小时/月
  - 15分钟无活动后休眠
  - ⚠️ 首次请求可能需要冷启动

- **Starter** (生产环境推荐)
  - 7 USD/月
  - 始终在线
  - 更快的响应速度

### 步骤5：创建服务

点击 **"Create Web Service"** 按钮

---

## 🔄 自动部署流程

### 触发部署

每次推送到 `main` 分支时，Render会自动：
1. ✅ 检测到新提交
2. ✅ 拉取最新代码
3. ✅ 执行构建命令
4. ✅ 重启服务
5. ✅ 部署完成

### 查看部署状态

在 Render Dashboard 中：
```
Services → audio-extractor-api → Events
```

可以看到：
- 部署日志
- 构建过程
- 错误信息（如果有）

---

## 🧪 验证部署

### 1. 获取服务URL

部署完成后，Render会提供一个URL，格式如：
```
https://audio-extractor-api.onrender.com
```

### 2. 测试健康检查

```bash
curl https://audio-extractor-api.onrender.com/api/health
```

**预期输出**:
```json
{
  "status": "healthy",
  "temp_dir": "/tmp/video_transcriber"
}
```

### 3. 测试音乐搜索功能

```bash
curl "https://audio-extractor-api.onrender.com/api/music/search?keyword=周杰伦&limit=5"
```

**预期输出**:
```json
{
  "songs": [
    {
      "id": 12345,
      "name": "七里香",
      "artist": "周杰伦",
      "album": "七里香",
      "duration": 300,
      "coverURL": "https://...",
      "audioURL": null
    }
  ]
}
```

### 4. 测试视频音频提取

```bash
curl -X POST https://audio-extractor-api.onrender.com/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xx411c7XD",
    "extract_audio": true,
    "audio_format": "m4a",
    "audio_quality": "good"
  }'
```

---

## 📱 iOS应用配置

### 更新服务器地址

在您的iOS应用中：

1. **打开设置页面**
   ```
   应用 → 设置 → 服务器配置
   ```

2. **更新URL**
   ```
   旧地址: https://vaizith.zeabur.app
   新地址: https://audio-extractor-api.onrender.com
   ```
   (将 `audio-extractor-api` 替换为您实际的服务名称)

3. **测试连接**
   - 点击"测试连接"按钮
   - 应该看到 ✅ 连接成功

4. **保存设置**

---

## 🔍 监控和日志

### 查看实时日志

在 Render Dashboard:
```
Services → audio-extractor-api → Logs
```

### 常用命令

**查看最近的部署**:
```
Services → audio-extractor-api → Events
```

**查看环境变量**:
```
Services → audio-extractor-api → Environment
```

**重新部署**:
```
Manual Deploy → Deploy latest commit
```

---

## 🐛 故障排查

### 问题1：部署失败

**检查**:
1. 查看构建日志
2. 确认 `requirements.txt` 格式正确
3. 检查Python版本兼容性

**解决**:
```bash
# 本地测试依赖安装
cd audio-extractor-cloud
pip install -r requirements.txt
```

### 问题2：服务无响应

**原因**: Free tier服务休眠

**解决**: 
- 首次访问需要等待30秒-1分钟
- 或升级到 Starter 计划

### 问题3：音乐搜索失败

**检查**:
```bash
curl https://your-service.onrender.com/api/music/search?keyword=test
```

**可能原因**:
- 网易云API限制
- 网络连接问题
- API镜像服务不可用

**解决**: 
- 等待几分钟后重试
- 检查日志中的错误信息

### 问题4：YouTube/抖音下载失败

**解决**: 配置Cookies

参考项目根目录的 `README.md` 中的说明：
- YouTube: 配置 `YT_COOKIES_*` 变量
- 抖音: 配置 `DY_COOKIES_*` 变量

---

## 🔐 安全建议

### 1. 保护您的GitHub Token

⚠️ **重要**: 您的GitHub Personal Access Token已配置在仓库中

**建议**:
```bash
# 移除URL中的token
cd /Users/enithz/Desktop/video/audio-extractor-cloud
git remote set-url origin https://github.com/aizithy/audio-extractor-cloud.git

# 配置credential helper
git config credential.helper store
```

然后在下次push时输入用户名和token。

### 2. 使用环境变量

- ✅ 敏感信息放在Render的环境变量中
- ✅ 不要提交cookies文件到仓库
- ✅ 定期更新access tokens

### 3. 限制访问

考虑添加API密钥验证：
```python
# 在main.py中添加
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.environ.get("API_KEY"):
        raise HTTPException(status_code=401)
```

---

## 📊 性能优化

### 1. 启用缓存

Render会自动缓存依赖包，加快后续部署。

### 2. 使用CDN

如果需要更快的全球访问速度，考虑在Render服务前加一层CDN。

### 3. 数据库

如果需要持久化数据，可以在Render上添加PostgreSQL数据库。

---

## 🔄 持续集成

### 自动部署触发

每次执行以下操作时自动部署：

```bash
# 1. 修改代码
# 2. 提交更改
git add .
git commit -m "你的提交信息"

# 3. 推送到GitHub
git push origin main

# 4. Render自动检测并部署 ✨
```

### 回滚到之前的版本

在 Render Dashboard:
```
Services → audio-extractor-api → Events → 选择之前的部署 → Rollback
```

---

## 📚 相关资源

### 官方文档
- [Render Python文档](https://render.com/docs/deploy-fastapi)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/render/)

### 项目文档
- `README.md` - 项目说明
- `README_DEPLOYMENT.md` - 部署详情
- `INTEGRATION_GUIDE.md` - 集成指南

---

## ✅ 部署完成检查清单

部署完成后，确认：

- [ ] 服务状态为 "Live"
- [ ] `/api/health` 返回正常
- [ ] `/api/music/search` 可以搜索音乐
- [ ] `/api/music/url` 可以获取播放URL
- [ ] `/api/music/lyric` 可以获取歌词
- [ ] `/api/process` 可以提取音频
- [ ] iOS应用可以连接到新服务器
- [ ] 音乐搜索功能正常工作

---

## 🎉 完成！

您的音乐搜索增强版后端服务已成功部署到Render！

**服务地址**: https://your-service-name.onrender.com

**下一步**:
1. 在iOS应用中更新服务器地址
2. 测试所有功能
3. 开始使用智能音乐搜索功能！

**享受您的音乐播放器！** 🎵

---

*部署时间: 2025-10-07*
*文档版本: 1.0*

