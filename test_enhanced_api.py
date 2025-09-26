#!/usr/bin/env python3
"""
增强版API测试脚本
测试B站、YouTube等平台的音频提取功能
"""

import requests
import time
import json
import sys
from typing import Dict, Any

class EnhancedAPITester:
    """增强版API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> Dict[str, Any]:
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 健康检查通过: {result['status']}")
            print(f"📊 支持的网站: {', '.join(result['supported_sites'][:5])}...")
            return result
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return {}
    
    def submit_task(self, url: str, extract_audio: bool = True, 
                   keep_video: bool = False, audio_format: str = "mp3") -> str:
        """提交处理任务"""
        print(f"📤 提交任务: {url}")
        
        payload = {
            "url": url,
            "extract_audio": extract_audio,
            "keep_video": keep_video,
            "audio_format": audio_format,
            "audio_quality": "good"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/process",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ 任务已提交: {task_id}")
            return task_id
        except Exception as e:
            print(f"❌ 提交任务失败: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"响应内容: {e.response.text}")
            return ""
    
    def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/status/{task_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 查询状态失败: {e}")
            return {}
    
    def wait_for_completion(self, task_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """等待任务完成"""
        print(f"⏳ 等待任务完成: {task_id}")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = self.check_task_status(task_id)
            if not status:
                break
            
            print(f"📊 进度: {status['progress']}% - {status['message']}")
            
            if status['status'] == 'completed':
                print("✅ 任务完成!")
                return status
            elif status['status'] == 'failed':
                print(f"❌ 任务失败: {status.get('error_detail', '未知错误')}")
                return status
            
            time.sleep(5)
        
        print("⏰ 等待超时")
        return {}
    
    def download_file(self, filename: str, save_path: str = None) -> bool:
        """下载文件"""
        if not save_path:
            save_path = filename
        
        print(f"📥 下载文件: {filename}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/download/{filename}",
                stream=True
            )
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 文件已保存: {save_path}")
            return True
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False
    
    def test_platform(self, platform_name: str, test_url: str, 
                     extract_audio: bool = True, keep_video: bool = False):
        """测试特定平台"""
        print(f"\n🎯 测试平台: {platform_name}")
        print("=" * 50)
        
        # 提交任务
        task_id = self.submit_task(test_url, extract_audio, keep_video)
        if not task_id:
            return False
        
        # 等待完成
        result = self.wait_for_completion(task_id)
        if not result or result['status'] != 'completed':
            return False
        
        # 显示结果
        print(f"🎬 视频标题: {result.get('video_title', 'N/A')}")
        print(f"⏱️ 视频时长: {result.get('duration', 0)}秒")
        
        if result.get('audio_file'):
            print(f"🎵 音频文件: {result['audio_file']}")
            # 可选：下载文件
            # self.download_file(result['audio_file'])
        
        if result.get('video_file'):
            print(f"🎥 视频文件: {result['video_file']}")
        
        return True

def run_comprehensive_test():
    """运行全面测试"""
    print("🚀 开始增强版API全面测试")
    print("=" * 60)
    
    tester = EnhancedAPITester()
    
    # 健康检查
    health = tester.test_health()
    if not health:
        print("❌ 健康检查失败，请确保服务正在运行")
        return
    
    # 测试平台列表
    test_cases = [
        {
            "platform": "Bilibili",
            "url": "https://www.bilibili.com/video/BV1xx411c7mD",  # 经典测试视频
            "extract_audio": True,
            "keep_video": False
        },
        # YouTube测试可能需要根据当前状况调整
        # {
        #     "platform": "YouTube",
        #     "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        #     "extract_audio": True,
        #     "keep_video": False
        # },
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        try:
            success = tester.test_platform(**test_case)
            if success:
                success_count += 1
            time.sleep(2)  # 短暂休息
        except KeyboardInterrupt:
            print("\n❌ 测试被用户中断")
            break
        except Exception as e:
            print(f"❌ 测试 {test_case['platform']} 时出错: {e}")
    
    # 测试结果
    print("\n" + "=" * 60)
    print(f"📊 测试完成: {success_count}/{total_tests} 成功")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")

def test_single_url():
    """测试单个URL"""
    if len(sys.argv) < 2:
        print("使用方法: python test_enhanced_api.py <video_url>")
        print("示例: python test_enhanced_api.py 'https://www.bilibili.com/video/BV1xx411c7mD'")
        return
    
    url = sys.argv[1]
    tester = EnhancedAPITester()
    
    print(f"🎯 测试单个URL: {url}")
    
    # 健康检查
    if not tester.test_health():
        return
    
    # 提交任务
    task_id = tester.submit_task(url, extract_audio=True, keep_video=True)
    if not task_id:
        return
    
    # 等待完成
    result = tester.wait_for_completion(task_id)
    if result and result['status'] == 'completed':
        print("\n🎉 测试成功完成!")
        print(f"🎬 标题: {result.get('video_title', 'N/A')}")
        print(f"🎵 音频: {result.get('audio_file', 'N/A')}")
        print(f"🎥 视频: {result.get('video_file', 'N/A')}")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            test_single_url()
        else:
            run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n👋 测试已停止")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
