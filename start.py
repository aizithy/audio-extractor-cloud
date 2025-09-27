#!/usr/bin/env python3
"""
增强版视频音频提取API服务启动脚本
"""

import sys
import subprocess
import platform
import os
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本检查通过: {sys.version}")
    return True

def check_ffmpeg():
    """检查FFmpeg是否安装"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg已安装")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️ FFmpeg未安装或不在PATH中")
    print("安装建议:")
    
    system = platform.system().lower()
    if system == "darwin":  # macOS
        print("  macOS: brew install ffmpeg")
    elif system == "linux":
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
    elif system == "windows":
        print("  Windows: 从 https://ffmpeg.org 下载并添加到PATH")
    
    print("或者继续运行，某些功能可能受限")
    return False

def install_dependencies():
    """安装Python依赖"""
    print("📦 检查Python依赖...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    try:
        subprocess.run([
            "python3", "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def create_temp_directory():
    """创建临时目录"""
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    print(f"✅ 临时目录已创建: {temp_dir}")

def start_server():
    """启动服务器"""
    print("🚀 启动增强版视频音频提取API服务...")
    print("=" * 50)
    
    # 切换到脚本目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        # 启动服务
        subprocess.run([
            "python3", "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("🎯 增强版视频音频提取API服务")
    print("=" * 50)
    
    # 环境检查
    if not check_python_version():
        return
    
    # 检查FFmpeg
    check_ffmpeg()
    
    # 安装依赖
    if not install_dependencies():
        return
    
    # 创建必要目录
    create_temp_directory()
    
    # 启动服务
    print("\n🎉 环境检查完成，启动服务...")
    print("访问地址:")
    print("  - 主页: http://localhost:8000")
    print("  - API文档: http://localhost:8000/docs")
    print("  - 健康检查: http://localhost:8000/api/health")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 50)
    
    start_server()

if __name__ == "__main__":
    main()
