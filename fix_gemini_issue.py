"""
修复 Gemini API 地理位置限制
尝试不同的 API 端点和模型
"""

import requests
import json
from PIL import Image
import io
import base64

API_KEY = "AIzaSyCT2swgK0wodZUfdWd1__DKO0wp2e8rFE8"

def try_api_v1():
    """尝试使用 v1 API"""
    print("\n尝试使用 v1 API...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
        response = requests.get(url, timeout=10)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ v1 API 连接成功")
            print(f"  模型数: {len(data.get('models', []))}")
            return True
        else:
            print(f"✗ 失败: {response.status_code}")
            print(f"  {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ 异常: {e}")
        return False

def try_generate_with_model(model_name, api_version="v1beta"):
    """尝试用指定模型生成内容"""
    print(f"\n尝试使用模型: {model_name} (API: {api_version})...")
    
    try:
        # 创建测试图像
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "简要描述"
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✓ {model_name} 成功")
            return True
        else:
            print(f"✗ {response.status_code}: {response.json().get('error', {}).get('message', 'Unknown')}")
            return False
    except Exception as e:
        print(f"✗ 异常: {e}")
        return False

def test_vision_only_api():
    """尝试使用 Vision-only API"""
    print("\n尝试使用 Vision-only 端点...")
    try:
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # 尝试 REST API
        url = f"https://generativelanguage.googleapis.com/v1/files?key={API_KEY}"
        
        files = {
            'file': ('image.jpg', buffer.getvalue(), 'image/jpeg')
        }
        
        response = requests.post(url, files=files, timeout=30)
        print(f"  上传文件状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ 可以上传文件")
            return True
        else:
            print(f"✗ {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 异常: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Gemini API 问题诊断 - 尝试修复")
    print("="*60)
    
    # 尝试不同方案
    try_api_v1()
    
    # 尝试不同的模型
    models_to_try = [
        ("gemini-pro-vision", "v1beta"),
        ("gemini-pro", "v1beta"),
        ("gemini-1.5-pro", "v1beta"),
        ("gemini-1.5-flash", "v1beta"),
        ("models/gemini-pro-vision", "v1beta"),
    ]
    
    for model, api_version in models_to_try:
        try_generate_with_model(model, api_version)
    
    # 尝试 Vision-only API
    test_vision_only_api()
    
    print("\n" + "="*60)
    print("建议:")
    print("="*60)
    print("\n如果以上都失败，可能是:")
    print("1. API Key 所在地区/国家不支持")
    print("2. 需要启用 'generative AI' API")
    print("3. 可能遇到访问限制")
    print("\n解决方案:")
    print("- 尝试使用 Claude 或 OpenAI 的 API")
    print("- 或者使用本地 LLaVA 模型")
