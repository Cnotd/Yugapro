"""
本地多模态 API 服务器示例
支持 LLaVA, Qwen 等多模态模型
安装依赖: pip install fastapi uvicorn pillow numpy requests

运行方式:
1. 安装 LLaVA: pip install llava-rlhf
2. 运行: python multimodal_server.py
3. 访问: http://localhost:8000/docs - FastAPI 文档
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
import io
import base64
import numpy as np
from typing import Optional

app = FastAPI(title="Multimodal Vision API", version="1.0")

# 全局变量 - 模型实例（如果需要）
model = None
processor = None


@app.on_event("startup")
async def startup():
    """应用启动时初始化模型"""
    global model, processor
    print("正在初始化多模态模型...")
    
    try:
        # 尝试加载 LLaVA 模型
        from transformers import AutoProcessor, LlavaForConditionalGeneration
        
        model_id = "llava-hf/llava-1.5-7b-hf"  # 或其他 LLaVA 模型
        processor = AutoProcessor.from_pretrained(model_id)
        model = LlavaForConditionalGeneration.from_pretrained(
            model_id,
            device_map="auto",
            load_in_4bit=True  # 使用 4-bit 量化以节省内存
        )
        print("✓ LLaVA 模型加载成功")
        
    except ImportError:
        print("√ 无法导入 transformers, 使用 mock 模式（开发用）")
        model = None
        processor = None
    except Exception as e:
        print(f"! 模型加载失败: {e}")
        model = None
        processor = None


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "multimodal-vision-api",
        "model_loaded": model is not None
    }


@app.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    分析图像
    
    参数:
    - image: 上传的图像文件
    - prompt: 分析提示词
    """
    try:
        # 读取上传的图像
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        
        if model is None or processor is None:
            # 使用 mock 模式返回结果（开发模式）
            return {
                "result": _mock_analysis(prompt),
                "status": "mock"
            }
        
        # 使用真实模型进行分析
        inputs = processor(images=img, text=prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=200)
        
        result = processor.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "result": result,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def chat_completions(body: dict):
    """
    LLaVA Vision API 兼容端点
    
    用法:
    {
        "model": "llava-1.5",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,..."}
                    },
                    {
                        "type": "text",
                        "text": "描述这个图像"
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    """
    try:
        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="缺少 messages")
        
        # 从消息中提取图像和文本
        user_message = messages[0].get("content", [])
        
        image_url = None
        text_prompt = ""
        
        for item in user_message:
            if item.get("type") == "image_url":
                image_url = item.get("image_url", {}).get("url")
            elif item.get("type") == "text":
                text_prompt = item.get("text", "")
        
        if not image_url or not text_prompt:
            raise HTTPException(status_code=400, detail="缺少图像或文本")
        
        # 处理 base64 图像
        if image_url.startswith("data:image"):
            # 提取 base64 数据
            base64_str = image_url.split(",")[1]
            image_data = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(image_data))
        else:
            raise HTTPException(status_code=400, detail="不支持的图像格式")
        
        # 获取分析结果
        if model is None or processor is None:
            analysis_result = _mock_analysis(text_prompt)
        else:
            inputs = processor(images=img, text=text_prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=body.get("max_tokens", 200))
            analysis_result = processor.decode(outputs[0], skip_special_tokens=True)
        
        return JSONResponse({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": analysis_result
                    }
                }
            ]
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/completions")
async def qwen_completions(body: dict):
    """
    Qwen 多模态 API 兼容端点
    
    用法: 与 /v1/chat/completions 相同
    """
    return await chat_completions(body)


def _mock_analysis(prompt: str) -> str:
    """
    模拟分析结果（开发模式）
    
    在没有真实模型的情况下返回示例结果
    """
    
    # 简单的模拟响应
    if "瑜伽" in prompt or "yoga" in prompt or "pose" in prompt.lower():
        return """根据图像分析，我观察到以下瑜伽姿态特征：

**姿态评估：**
- 脊柱对齐: 优秀 - 保持良好的中立脊柱，没有过度弯曲
- 肩膀对齐: 好 - 肩膀平衡，略微向后
- 髋部对齐: 很好 - 髋部良好对齐，没有旋转
- 膝盖弯曲: 适当 - 膝盖与脚趾对齐
- 脚的位置: 稳定 - 脚宽度与髋部同宽

**问题识别：**
1. 核心参与度可以更强
2. 肩膀可以稍微放松

**改进建议：**
1. 增强核心肌肉参与，想象将腹部向脊柱方向收紧
2. 深呼吸，让肩膀自然放松
3. 将注意力集中在脚对地面的感受
4. 确保整个脊柱保持长拉伸

**总体评分：** 78/100
"""
    else:
        return """根据图像分析：
这是一个示例分析结果。
在实际模型中，这里会有详细的多模态分析。
"""


if __name__ == "__main__":
    print("\n" + "="*60)
    print("启动本地多模态 API 服务器")
    print("地址: http://localhost:8000")
    print("文档: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
