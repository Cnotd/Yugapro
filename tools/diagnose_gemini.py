"""
Gemini API 诊断脚本
"""

import requests
from PIL import Image
import io
import base64
import os

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-1.5-flash"

def diagnose():
    print("\n" + "="*60)
    print("Gemini API 诊断")
    print("="*60)
    if not API_KEY:
        print("未设置 GEMINI_API_KEY，跳过需要鉴权的诊断。")
        return
    
    # 1. 检查网络连接
    print("\n1. 检查网络连接...")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print("✓ 网络连接正常")
    except Exception as e:
        print(f"✗ 网络连接失败: {e}")
        return
    
    # 2. 验证 API Key 格式
    print("\n2. 验证 API Key...")
    if API_KEY.startswith("AIzaSy"):
        print(f"✓ API Key 格式正确 (前缀: AIzaSy...)")
        print(f"  - 长度: {len(API_KEY)}")
    else:
        print(f"✗ API Key 格式不对，应以 AIzaSy 开头")
        return
    
    # 3. 测试列出模型
    print("\n3. 测试列出可用模型...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        response = requests.get(url, timeout=10)
        print(f"  - 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"✓ 成功获取模型列表，共 {len(models)} 个")
            
            # 显示前几个模型
            print("\n  可用的模型:")
            for model in models[:5]:
                print(f"    - {model.get('name', 'Unknown')}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
            print(f"  响应: {response.text[:500]}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")
        return
    
    # 4. 尝试发送测试请求
    print("\n4. 尝试发送图像分析请求...")
    try:
        # 创建测试图像
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "简要描述这个图像"
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generation_config": {
                "temperature": 0.7,
                "max_output_tokens": 100
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"  - 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ 请求成功")
            result = response.json()
            
            # 提取响应
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', '')
                print(f"  - 响应文本: {text[:100]}...")
            else:
                print(f"  - 响应: {result}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)

if __name__ == "__main__":
    diagnose()
