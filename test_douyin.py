#!/usr/bin/env python3
"""
Test script for Douyin cookies functionality
"""
import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import _is_douyin_url, _ydl_opts

def test_douyin_url_detection():
    """Test Douyin URL detection"""
    print("Testing Douyin URL detection...")

    # Test valid Douyin URLs
    valid_urls = [
        "https://www.douyin.com/video/7553219229652520251",
        "https://v.douyin.com/abc123/",
        "https://iesdouyin.com/share/video/123456789/",
    ]

    for url in valid_urls:
        if _is_douyin_url(url):
            print(f"✓ {url}")
        else:
            print(f"✗ {url}")

    # Test invalid URLs
    invalid_urls = [
        "https://www.youtube.com/watch?v=abc123",
        "https://www.bilibili.com/video/av123",
        "https://example.com",
    ]

    for url in invalid_urls:
        if not _is_douyin_url(url):
            print(f"✓ {url} (correctly rejected)")
        else:
            print(f"✗ {url} (incorrectly accepted)")

def test_douyin_cookies_handling():
    """Test Douyin cookies handling in _ydl_opts"""
    print("\nTesting Douyin cookies handling...")

    # Create a temporary cookies file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("douyin.com\tTRUE\t/\tFALSE\t0\tsessionid\ttest_session_123\n")
        temp_cookies_file = f.name

    try:
        # Test with DY_COOKIES_FILE
        os.environ['DY_COOKIES_FILE'] = temp_cookies_file
        opts = _ydl_opts('/tmp/test', 'm4a', 'good', 'https://www.douyin.com/video/test')

        if 'cookiefile' in opts and opts['cookiefile'].endswith('dy_cookies.txt'):
            print("✓ DY_COOKIES_FILE handling works")
        else:
            print("✗ DY_COOKIES_FILE handling failed")

        # Test with DY_COOKIES_B64
        del os.environ['DY_COOKIES_FILE']
        os.environ['DY_COOKIES_B64'] = 'dGVzdCBjb29raWVz'  # base64 of "test cookies"
        opts = _ydl_opts('/tmp/test', 'm4a', 'good', 'https://www.douyin.com/video/test')

        if 'cookiefile' in opts and opts['cookiefile'].endswith('dy_cookies.txt'):
            print("✓ DY_COOKIES_B64 handling works")
        else:
            print("✗ DY_COOKIES_B64 handling failed")

        # Clean up environment variables
        if 'DY_COOKIES_FILE' in os.environ:
            del os.environ['DY_COOKIES_FILE']
        if 'DY_COOKIES_B64' in os.environ:
            del os.environ['DY_COOKIES_B64']

    finally:
        # Clean up temporary file
        Path(temp_cookies_file).unlink(missing_ok=True)

if __name__ == "__main__":
    test_douyin_url_detection()
    test_douyin_cookies_handling()
    print("\nAll tests completed!")
