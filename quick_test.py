#!/usr/bin/env python3
"""
快速测试脚本 - 测试部署后的API服务
"""

import requests
import time
import sys
import json

def test_deployed_api(base_url):
    """测试部署后的API服务"""
    
    print(f"🧪 测试部署的API服务: {base_url}")
    print("=" * 50)
    
    # 1. 健康检查
    print("1. 健康检查...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务状态: {data['status']}")
            print(f"📁 临时文件: {data.get('temp_files', 0)}个")
            print(f"⚡ 活跃任务: {data.get('active_tasks', 0)}个")
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    # 2. 测试异步API
    print("\n2. 测试异步音频提取...")
    test_url = "https://www.bilibili.com/video/BV1xx411c7mD"
    
    try:
        payload = {
            "url": test_url,
            "extract_audio": True,
            "keep_video": False,
            "audio_format": "mp3",
            "audio_quality": "good"
        }
        
        print(f"📤 提交任务: {test_url}")
        response = requests.post(f"{base_url}/api/process", 
                               json=payload, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data["task_id"]
            print(f"✅ 任务已提交: {task_id}")
            
            # 查询任务状态
            print("📊 监控任务进度...")
            for i in range(30):  # 最多等待5分钟
                time.sleep(10)
                try:
                    status_response = requests.get(f"{base_url}/api/status/{task_id}", 
                                                 timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        progress = status_data.get('progress', 0)
                        message = status_data.get('message', '')
                        status = status_data.get('status', '')
                        
                        print(f"📈 进度: {progress}% - {message}")
                        
                        if status == 'completed':
                            print("🎉 任务完成!")
                            audio_file = status_data.get('audio_file')
                            if audio_file:
                                download_url = f"{base_url}/api/download/{audio_file}"
                                print(f"🎵 下载链接: {download_url}")
                            return True
                        elif status == 'failed':
                            error_detail = status_data.get('error_detail', '未知错误')
                            print(f"❌ 任务失败: {error_detail}")
                            return False
                    else:
                        print("❌ 查询状态失败")
                        return False
                except Exception as e:
                    print(f"❌ 查询状态出错: {e}")
                    return False
            
            print("⏰ 任务超时")
            return False
            
        else:
            print(f"❌ 提交任务失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 异步API测试失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python3 quick_test.py <API_BASE_URL>")
        print("示例: python3 quick_test.py https://your-domain.zeabur.app")
        return
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚀 增强版视频音频提取API - 快速测试")
    print("=" * 50)
    print(f"测试URL: {base_url}")
    print()
    
    success = test_deployed_api(base_url)
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过! API服务运行正常")
        print("\n📖 接下来您可以:")
        print(f"  - 访问API文档: {base_url}/docs")
        print(f"  - 在iOS应用中配置: {base_url}")
        print(f"  - 测试其他视频平台")
    else:
        print("❌ 测试失败，请检查:")
        print("  1. API服务是否正常运行")
        print("  2. 网络连接是否正常")
        print("  3. URL是否正确")
        print(f"  4. 访问健康检查: {base_url}/api/health")

if __name__ == "__main__":
    main()
