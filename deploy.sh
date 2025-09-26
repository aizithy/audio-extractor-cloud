#!/bin/bash
# 增强版视频音频提取API - 部署脚本

echo "🚀 增强版视频音频提取API - 部署助手"
echo "============================================"

# 检查Git状态
if [ ! -d ".git" ]; then
    echo "❌ 错误: 当前目录不是Git仓库"
    exit 1
fi

# 获取GitHub用户名
echo ""
read -p "请输入您的GitHub用户名: " github_username

if [ -z "$github_username" ]; then
    echo "❌ 错误: GitHub用户名不能为空"
    exit 1
fi

# 设置仓库名称
repo_name="enhanced-video-audio-api"
github_url="https://github.com/$github_username/$repo_name.git"

echo ""
echo "📋 部署信息确认:"
echo "GitHub用户名: $github_username"
echo "仓库名称: $repo_name"
echo "仓库URL: $github_url"
echo ""

read -p "确认信息正确? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ 部署已取消"
    exit 1
fi

# 检查是否已经添加了remote
if git remote get-url origin &>/dev/null; then
    echo "⚠️  检测到已存在的远程仓库"
    git remote -v
    read -p "是否要更新远程仓库地址? (y/N): " update_remote
    if [[ $update_remote =~ ^[Yy]$ ]]; then
        git remote set-url origin $github_url
        echo "✅ 远程仓库地址已更新"
    fi
else
    # 添加远程仓库
    echo "📡 添加远程仓库..."
    git remote add origin $github_url
    echo "✅ 远程仓库已添加"
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 检测到未提交的更改，正在提交..."
    git add .
    git commit -m "chore: 部署前更新"
fi

# 推送到GitHub
echo "📤 推送代码到GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ 代码推送成功!"
else
    echo "❌ 代码推送失败，请检查以下几点:"
    echo "   1. GitHub仓库是否已创建: https://github.com/$github_username/$repo_name"
    echo "   2. 是否有推送权限"
    echo "   3. 网络连接是否正常"
    exit 1
fi

echo ""
echo "🎉 GitHub部署完成!"
echo "============================================"
echo ""
echo "📋 下一步 - Zeabur部署:"
echo "1. 访问 Zeabur: https://zeabur.com"
echo "2. 登录/注册账户"
echo "3. 点击 'New Project'"
echo "4. 选择 'Deploy from GitHub'"
echo "5. 选择仓库: $github_username/$repo_name"
echo "6. 等待自动部署完成"
echo ""
echo "🔗 仓库链接: https://github.com/$github_username/$repo_name"
echo ""
echo "📖 部署完成后，您可以:"
echo "   - 访问API文档: https://your-domain.zeabur.app/docs"
echo "   - 健康检查: https://your-domain.zeabur.app/api/health"
echo "   - 测试音频提取功能"
echo ""
echo "🎯 示例API调用:"
echo "curl -X POST 'https://your-domain.zeabur.app/api/process' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"url\": \"https://www.bilibili.com/video/BV1xx411c7mD\", \"extract_audio\": true}'"

# 打开GitHub仓库
if command -v open &> /dev/null; then
    read -p "是否在浏览器中打开GitHub仓库? (y/N): " open_browser
    if [[ $open_browser =~ ^[Yy]$ ]]; then
        open "https://github.com/$github_username/$repo_name"
    fi
fi

echo ""
echo "✨ 部署脚本执行完成!"
