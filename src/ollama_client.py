"""
Ollama客户端模块
封装Ollama API调用,用于与大模型交互
"""

import requests
import base64
from typing import Optional, Dict
import io
from PIL import Image

from config.settings import OLLAMA_CONFIG


class OllamaClient:
    """Ollama API客户端"""
    
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        """
        初始化Ollama客户端
        
        Args:
            host: Ollama服务地址
            model: 使用的模型名称
        """
        self.host = host or OLLAMA_CONFIG["host"]
        self.model = model or OLLAMA_CONFIG["model"]
        self.timeout = OLLAMA_CONFIG["timeout"]
        self.temperature = OLLAMA_CONFIG["temperature"]
    
    def generate(self, prompt: str, image: Optional[object] = None) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 提示词
            image: 图像对象 (PIL.Image或numpy array)
            
        Returns:
            response: 模型响应文本
            
        Raises:
            ConnectionError: 无法连接到Ollama服务
            TimeoutError: 请求超时
            Exception: 其他错误
        """
        # 准备请求数据
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        # 如果有图像,添加到请求中
        if image is not None:
            image_base64 = self._image_to_base64(image)
            data["images"] = [image_base64]
        
        # 发送请求
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到Ollama服务: {self.host}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求超时 (>{self.timeout}秒)")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")
    
    def _image_to_base64(self, image: object) -> str:
        """
        将图像转换为base64编码
        
        Args:
            image: 图像对象 (PIL.Image或numpy array)
            
        Returns:
            base64编码的图像字符串
        """
        # 如果是numpy数组,转换为PIL.Image
        if hasattr(image, 'shape'):  # numpy array
            from PIL import Image
            import numpy as np
            image = Image.fromarray(np.uint8(image))
        
        # 调整图像大小以加快推理速度（最大边长252像素）
        original_size = image.size
        max_dimension = max(original_size)
        if max_dimension > 252:
            scale = 252 / max_dimension
            new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 转换为base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
    
    def chat(self, messages: list) -> str:
        """
        对话模式生成
        
        Args:
            messages: 消息列表,每个消息包含role和content
            
        Returns:
            response: 模型响应文本
        """
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
        
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到Ollama服务: {self.host}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求超时 (>{self.timeout}秒)")
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")
    
    def check_connection(self) -> bool:
        """
        检查Ollama服务是否可用
        
        Returns:
            是否可用
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list:
        """
        列出可用的模型
        
        Returns:
            模型列表
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except:
            return []
    
    def get_model_info(self) -> Dict:
        """
        获取当前模型信息
        
        Returns:
            模型信息字典
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            result = response.json()
            
            models = result.get("models", [])
            for model in models:
                if self.model in model.get("name", ""):
                    return model
            
            return {}
        except:
            return {}
