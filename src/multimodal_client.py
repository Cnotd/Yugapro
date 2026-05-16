"""
多模态 API 客户端模块
支持线上和本地多模态模型（OpenAI Vision, Claude, Gemini, LLaVA, Qwen 等）
用于视频帧和文本的多模态分析
"""

import requests
import base64
import json
from typing import Optional, Dict, Any
from PIL import Image
import io
import numpy as np

from config.settings import MULTIMODAL_CONFIG


class MultimodalClient:
    """多模态 API 客户端 - 支持云端和本地 API"""
    
    def __init__(self, api_url: Optional[str] = None, model: Optional[str] = None, api_type: Optional[str] = None, api_key: Optional[str] = None):
        """
        初始化多模态客户端
        
        Args:
            api_url: API 服务地址（云端 URL 或本地地址）
            model: 使用的模型名称
            api_type: API 类型 ('openai', 'claude', 'gemini', 'llamavision', 'qwen', 'generic')
            api_key: API 密钥（用于云端 API）
        """
        self.api_url = api_url or MULTIMODAL_CONFIG.get("api_url", "http://localhost:8000")
        self.model = model or MULTIMODAL_CONFIG.get("model", "gpt-4-vision")
        self.api_type = api_type or MULTIMODAL_CONFIG.get("api_type", "openai")
        self.api_key = api_key or MULTIMODAL_CONFIG.get("api_key", None)
        self.timeout = MULTIMODAL_CONFIG.get("timeout", 120)
        self.temperature = MULTIMODAL_CONFIG.get("temperature", 0.7)
        
        print(f"[MultimodalClient] 初始化中...")
        print(f"  - API 类型: {self.api_type}")
        print(f"  - 模型: {self.model}")
        if self.api_url.startswith("http"):
            is_local = "localhost" in self.api_url or "127.0.0.1" in self.api_url
            print(f"  - 地址: {self.api_url} ({'本地' if is_local else '线上'})")
    
    def check_connection(self) -> bool:
        """检查与 API 的连接"""
        try:
            if self.api_type in {"openai", "claude", "gemini", "qwen"} and not self.api_key:
                return False
            if self.api_type == "openai":
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
                return response.status_code < 400
            elif self.api_type == "claude":
                headers = {"x-api-key": self.api_key}
                response = requests.get("https://api.anthropic.com/v1/models", headers=headers, timeout=5)
                return response.status_code < 400
            elif self.api_type == "gemini":
                response = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}", timeout=5)
                return response.status_code < 400
            elif self.api_type == "qwen":
                # 检查阿里云百炼 Qwen API
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.get(f"{self.api_url}/models", headers=headers, timeout=5)
                return response.status_code < 400
            else:
                # 本地或其他 API
                response = requests.get(f"{self.api_url}/health", timeout=5)
                return response.status_code < 400
        except Exception as e:
            print(f"[MultimodalClient] 连接失败: {e}")
            return False
    
    def analyze_image_with_prompt(self, image: Any, prompt: str) -> str:
        """
        使用提示词分析图像
        
        Args:
            image: 图像对象 (PIL.Image 或 numpy array)
            prompt: 提示词/问题
            
        Returns:
            分析结果文本
        """
        # 所有供应商接口统一接收 base64 图像，便于在不同模型之间切换。
        image_base64 = self._image_to_base64(image)
        
        # 根据配置选择具体的多模态服务，业务层不需要关心厂商协议差异。
        if self.api_type == "openai":
            return self._openai_request(image_base64, prompt)
        elif self.api_type == "claude":
            return self._claude_request(image_base64, prompt)
        elif self.api_type == "gemini":
            return self._gemini_request(image_base64, prompt)
        elif self.api_type == "llamavision":
            return self._llamavision_request(image_base64, prompt)
        elif self.api_type == "qwen":
            return self._qwen_request(image_base64, prompt)
        else:
            return self._generic_request(image_base64, prompt)
    
    def _openai_request(self, image_base64: str, prompt: str) -> str:
        """调用 OpenAI Vision API (gpt-4-vision, gpt-4o)"""
        try:
            print("[OpenAI Vision] 发送请求中...")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,  # gpt-4-vision 或 gpt-4o
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print("[OpenAI Vision] 请求成功")
            return result['choices'][0]['message']['content']
        
        except Exception as e:
            raise Exception(f"OpenAI Vision API 请求失败: {str(e)}")
    
    def _claude_request(self, image_base64: str, prompt: str) -> str:
        """调用 Claude Vision API"""
        try:
            print("[Claude Vision] 发送请求中...")
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print("[Claude Vision] 请求成功")
            return result['content'][0]['text']
        
        except Exception as e:
            raise Exception(f"Claude Vision API 请求失败: {str(e)}")
    
    def _gemini_request(self, image_base64: str, prompt: str) -> str:
        """调用 Google Gemini Vision API (v1)"""
        try:
            print("[Gemini Vision] 发送请求中...")
            
            # Gemini v1 API 使用 generationConfig 而非 generation_config
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
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
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": 2000
                }
            }
            
            # 使用 v1 API（url 中已包含 /v1）
            url = f"{self.api_url}/models/{self.model}:generateContent"
            if "?" in url:
                url = f"{url}&key={self.api_key}"
            else:
                url = f"{url}?key={self.api_key}"
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print("[Gemini Vision] 请求成功")
            
            # 提取响应文本
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0].get('content', {})
                if 'parts' in content and len(content['parts']) > 0:
                    return content['parts'][0].get('text', '')
            
            raise Exception("无效的 API 响应格式")
        
        except Exception as e:
            raise Exception(f"Gemini Vision API 请求失败: {str(e)}")
    
    def _llamavision_request(self, image_base64: str, prompt: str) -> str:
        """调用 LLaVA Vision API (本地或线上)"""
        try:
            print("[LLaVA Vision] 发送请求中...")
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print("[LLaVA Vision] 请求成功")
            return result['choices'][0]['message']['content']
        
        except Exception as e:
            raise Exception(f"LLaVA Vision API 请求失败: {str(e)}")
    
    def _qwen_request(self, image_base64: str, prompt: str) -> str:
        """调用阿里云百炼 Qwen 多模态 API"""
        try:
            print("[Qwen VL] 发送请求中...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 阿里云百炼 Qwen VL API 格式，图像和文本放在同一条 user 消息中。
            payload = {
                "model": self.model,  # qwen-vl-max, qwen-vl-plus
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image",
                                    "image": f"data:image/jpeg;base64,{image_base64}"
                                }
                            ]
                        }
                    ]
                },
                "parameters": {
                    "temperature": self.temperature,
                    "max_output_tokens": 2000
                }
            }
            
            # 阿里云百炼官方 API 端点
            url = f"{self.api_url}/services/aigc/multimodal-generation/generation"
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print("[Qwen VL] 请求成功")
            
            # 解析阿里云 API 响应格式
            if result.get('code') == '200' or 'output' in result:
                output = result.get('output', {})
                if 'choices' in output and len(output['choices']) > 0:
                    choice = output['choices'][0]
                    if 'message' in choice:
                        content = choice['message'].get('content', [])
                        if isinstance(content, list) and len(content) > 0:
                            return content[0].get('text', '')
                        elif isinstance(content, str):
                            return content
            
            raise Exception(f"无法解析 Qwen 响应: {result}")
        
        except Exception as e:
            raise Exception(f"Qwen VL API 请求失败: {str(e)}")
    
    def _generic_request(self, image_base64: str, prompt: str) -> str:
        """调用通用多模态 API"""
        try:
            print("[Generic] 发送请求中...")
            payload = {
                "model": self.model,
                "image": f"data:image/jpeg;base64,{image_base64}",
                "prompt": prompt,
                "temperature": self.temperature
            }
            
            response = requests.post(
                f"{self.api_url}/analyze",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print("[Generic] 请求成功")
            
            # 尝试多种可能的响应格式
            if 'result' in result:
                return result['result']
            elif 'response' in result:
                return result['response']
            elif 'text' in result:
                return result['text']
            else:
                return json.dumps(result)
        
        except Exception as e:
            raise Exception(f"通用多模态 API 请求失败: {str(e)}")
    
    def _image_to_base64(self, image: Any) -> str:
        """
        将图像转换为 base64 编码
        
        Args:
            image: 图像对象 (PIL.Image 或 numpy array)
            
        Returns:
            base64 编码的图像字符串
        """
        # 评估流水线可能传入 numpy 帧，也可能传入 PIL 图像，这里统一转成 JPEG。
        if isinstance(image, np.ndarray):
            image = Image.fromarray(np.uint8(image))
        
        # 调整图像大小以加快推理速度（最大边长 1024 像素）
        max_size = 1024
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 转换为 JPEG 格式以节省空间
        buffer = io.BytesIO()
        image.convert('RGB').save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # 编码为 base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    
    def analyze_frame_sequence(self, frames: list, prompt: str) -> str:
        """
        分析多帧图像序列（取关键帧）
        
        Args:
            frames: 图像列表
            prompt: 提示词
            
        Returns:
            分析结果
        """
        if not frames:
            raise ValueError("框架列表为空")
        
        # 取中间帧作为关键帧
        key_frame_idx = len(frames) // 2
        key_frame = frames[key_frame_idx]
        
        return self.analyze_image_with_prompt(key_frame, prompt)
