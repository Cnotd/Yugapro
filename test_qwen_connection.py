#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 Qwen API 连接"""

import requests
import json

API_KEY = "sk-eed0f038ff904cb09c4b3ae20bbf815d"
API_URL = "https://dashscope.aliyuncs.com/api/v1"
MODEL = "qwen-vl-max"

print("=" * 60)
print("Qwen API 连接诊断")
print("=" * 60)

# 测试 1: 基本连接性
print("\n[测试 1] 基本连接性...")
try:
    response = requests.get(API_URL, timeout=10)
    print(f"✓ 基本连接: {response.status_code}")
except Exception as e:
    print(f"✗ 基本连接失败: {e}")

# 测试 2: 列出模型
print("\n[测试 2] 列出可用模型...")
try:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/models"
    response = requests.get(url, headers=headers, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"✗ 列出模型失败: {e}")

# 测试 3: 测试文本生成（不需要图像）
print("\n[测试 3] 测试文本生成...")
try:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-vl-max",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "说说你好吗"
                        }
                    ]
                }
            ]
        },
        "parameters": {
            "temperature": 0.7,
            "max_output_tokens": 100
        }
    }
    
    url = f"{API_URL}/services/aigc/multimodal-generation/generation"
    print(f"请求 URL: {url}")
    print(f"请求头: {headers}")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)[:300]}")
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"✓ 状态码: {response.status_code}")
    print(f"响应: {response.text[:1000]}")
except Exception as e:
    print(f"✗ 文本生成失败: {e}")

print("\n" + "=" * 60)
