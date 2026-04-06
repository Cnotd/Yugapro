"""
多模态 API 测试脚本
用于测试各种线上和本地多模态 API 连接
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.multimodal_client import MultimodalClient
from config.settings import MULTIMODAL_CONFIG
import numpy as np
from PIL import Image
import io


def create_test_image():
    """创建测试图像（简单的彩色方块）"""
    img = Image.new('RGB', (256, 256), color=(73, 109, 137))
    
    # 添加一些文本
    try:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((50, 110), "Test Image", fill=(255, 255, 255))
    except:
        pass
    
    return img


def test_api_connection():
    """测试 API 连接"""
    print("\n" + "="*60)
    print("多模态 API 连接测试")
    print("="*60)
    
    print(f"\n当前配置:")
    print(f"  - API 类型: {MULTIMODAL_CONFIG.get('api_type', 'unknown')}")
    print(f"  - 模型: {MULTIMODAL_CONFIG.get('model', 'unknown')}")
    print(f"  - 地址: {MULTIMODAL_CONFIG.get('api_url', 'unknown')}")
    
    # 创建客户端
    try:
        client = MultimodalClient()
        print("\n✓ 客户端初始化成功")
    except Exception as e:
        print(f"\n✗ 客户端初始化失败: {e}")
        return False
    
    # 测试连接
    print("\n正在测试 API 连接...")
    if client.check_connection():
        print("✓ API 连接成功")
    else:
        print("✗ API 连接失败")
        print("\n  请检查:")
        print("  - API Key 是否正确配置")
        print("  - 网络连接是否正常")
        print("  - API 端点地址是否正确")
        return False
    
    # 测试分析功能
    print("\n正在测试图像分析...")
    try:
        test_image = create_test_image()
        prompt = "简要描述这个图像"
        
        result = client.analyze_image_with_prompt(test_image, prompt)
        
        print("✓ 图像分析成功")
        print(f"\n返回结果（前 200 字符）:\n{result[:200]}...")
        
        return True
    
    except Exception as e:
        print(f"✗ 图像分析失败: {e}")
        return False


def test_yoga_analysis():
    """测试瑜伽分析（需要真实的瑜伽图像）"""
    print("\n" + "="*60)
    print("瑜伽姿态分析测试")
    print("="*60)
    
    try:
        client = MultimodalClient()
        
        # 创建或加载瑜伽姿态图像
        test_image = create_test_image()
        
        # 瑜伽评估提示词
        prompt = """请分析这个瑜伽姿态图像，并提供以下评估：

姿态: Mountain Pose
检测质量: 37.5%

关键角度（单位：度）:
- Hip: 平均 175.2°（标准 170-180°）
- Knee: 平均 172.5°（标准 165-180°）
- Shoulder: 平均 177.8°（标准 170-180°）
- Spine: 平均 5.3°（标准 0-10°）

稳定性评分: 75/100

请返回以下内容（JSON 格式）:
{
    "total_score": 85,
    "structure_score": 50,
    "alignment_score": 25,
    "stability_score": 10,
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}"""
        
        print("正在分析瑜伽姿态...")
        result = client.analyze_image_with_prompt(test_image, prompt)
        
        print("✓ 分析成功")
        print(f"\n返回结果:\n{result}")
        
        return True
    
    except Exception as e:
        print(f"✗ 分析失败: {e}")
        return False


def list_available_apis():
    """列出支持的 API 类型"""
    print("\n" + "="*60)
    print("支持的 API 类型")
    print("="*60)
    
    apis = {
        "openai": {
            "name": "OpenAI Vision",
            "models": ["gpt-4-vision", "gpt-4o"],
            "cost": "$0.005-0.03 per request",
            "doc": "https://platform.openai.com/docs/guides/vision"
        },
        "claude": {
            "name": "Claude Vision",
            "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "cost": "$0.0008-0.045 per request",
            "doc": "https://docs.anthropic.com/claude/reference/vision"
        },
        "gemini": {
            "name": "Google Gemini",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "cost": "Free - $10/month",
            "doc": "https://ai.google.dev/"
        },
        "llamavision": {
            "name": "LLaVA Vision (Local)",
            "models": ["llava-1.5", "llava-1.6"],
            "cost": "Free (local)",
            "doc": "https://github.com/haotian-liu/LLaVA"
        },
        "qwen": {
            "name": "Qwen Multi-modal",
            "models": ["qwen-vl-plus", "qwen-vl-max"],
            "cost": "Varies",
            "doc": "https://dashscope.aliyun.com"
        }
    }
    
    for api_type, info in apis.items():
        print(f"\n{api_type.upper()}")
        print(f"  名称: {info['name']}")
        print(f"  模型: {', '.join(info['models'])}")
        print(f"  成本: {info['cost']}")
        print(f"  文档: {info['doc']}")


def show_configuration_examples():
    """显示配置示例"""
    print("\n" + "="*60)
    print("配置示例")
    print("="*60)
    
    examples = {
        "OpenAI": """
MULTIMODAL_CONFIG = {
    "api_url": "https://api.openai.com/v1",
    "model": "gpt-4o",
    "api_type": "openai",
    "api_key": "sk-your-key",
}""",
        "Claude": """
MULTIMODAL_CONFIG = {
    "api_url": "https://api.anthropic.com",
    "model": "claude-3-sonnet-20240229",
    "api_type": "claude",
    "api_key": "sk-ant-your-key",
}""",
        "Gemini": """
MULTIMODAL_CONFIG = {
    "api_url": "https://generativelanguage.googleapis.com",
    "model": "gemini-1.5-flash",
    "api_type": "gemini",
    "api_key": "AIzaSy_your_key",
}""",
        "Local LLaVA": """
MULTIMODAL_CONFIG = {
    "api_url": "http://localhost:8000",
    "model": "llava-1.5",
    "api_type": "llamavision",
    "api_key": None,
}"""
    }
    
    for name, config in examples.items():
        print(f"\n{name}:")
        print(config)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试多模态 API 连接")
    parser.add_argument("--test-connection", action="store_true", help="测试 API 连接")
    parser.add_argument("--test-yoga", action="store_true", help="测试瑜伽分析")
    parser.add_argument("--list-apis", action="store_true", help="列出支持的 API")
    parser.add_argument("--show-config", action="store_true", help="显示配置示例")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    
    args = parser.parse_args()
    
    if not any([args.test_connection, args.test_yoga, args.list_apis, args.show_config, args.all]):
        args.all = True
    
    if args.list_apis or args.all:
        list_available_apis()
    
    if args.show_config or args.all:
        show_configuration_examples()
    
    if args.test_connection or args.all:
        success = test_api_connection()
        if not success and not args.all:
            sys.exit(1)
    
    if args.test_yoga or args.all:
        if args.test_connection or args.all:
            print("\n")  # 空行分隔
        test_yoga_analysis()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
