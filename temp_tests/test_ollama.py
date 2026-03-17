"""
测试本地大模型(Ollama)是否可用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ollama_client import OllamaClient

def test_ollama():
    print("=" * 60)
    print("Ollama 本地大模型测试")
    print("=" * 60)
    
    # 初始化客户端
    client = OllamaClient()
    
    # 1. 检查连接
    print("\n1. 检查Ollama服务连接...")
    if client.check_connection():
        print("✓ Ollama服务运行正常")
    else:
        print("✗ 无法连接到Ollama服务")
        print("\n请确保:")
        print("  1. Ollama已安装: https://ollama.ai/")
        print("  2. Ollama服务正在运行")
        print("  3. 可以访问: http://localhost:11434")
        return False
    
    # 2. 列出可用模型
    print("\n2. 检查可用模型...")
    models = client.list_models()
    
    if models:
        print(f"✓ 找到 {len(models)} 个可用模型:")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model.get('name', 'Unknown')}")
    else:
        print("⚠ 未找到可用模型")
        print("\n建议拉取一个模型:")
        print("  ollama pull qwen:7b")
        print("  或")
        print("  ollama pull llama3:8b")
        return False
    
    # 3. 测试文本生成
    print("\n3. 测试文本生成...")
    try:
        test_prompt = "你好,请用一句话介绍你自己"
        response = client.generate(test_prompt)
        
        print(f"✓ 文本生成成功")
        print(f"\n模型回复:")
        print(f"  {response[:100]}...")
    except Exception as e:
        print(f"✗ 文本生成失败: {e}")
        return False
    
    # 4. 测试多模态(如果有支持视觉的模型)
    print("\n4. 检查模型是否支持视觉...")
    has_vision_model = False
    vision_models = ["qwen", "llava", "bakllava", "minicpm"]
    
    for model in models:
        model_name = model.get('name', '').lower()
        if any(vm in model_name for vm in vision_models):
            print(f"✓ 找到支持视觉的模型: {model.get('name')}")
            has_vision_model = True
            break
    
    if not has_vision_model:
        print("⚠ 未找到支持视觉的模型")
        print("\n建议安装支持视觉的模型:")
        print("  ollama pull qwen:7b")
        print("  或")
        print("  ollama pull llava:7b")
        print("\n注意: 不支持视觉的模型无法分析图像")
    
    # 5. 获取当前模型信息
    print("\n5. 当前配置的模型信息...")
    model_info = client.get_model_info()
    if model_info:
        print(f"✓ 模型名称: {model_info.get('name', 'Unknown')}")
        if 'size' in model_info:
            print(f"  模型大小: {model_info['size'] / (1024**3):.2f} GB")
    else:
        print(f"ℹ 当前配置模型: {client.model}")
        print("  (未找到详细信息)")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    if has_vision_model:
        print("\n✓ 您的系统已完全配置,可以使用AI评估功能")
    else:
        print("\n⚠ 基础功能可用,但建议安装支持视觉的模型以获得完整功能")
    
    print(f"\n访问瑜伽评估系统: http://localhost:5000")
    
    return True


if __name__ == "__main__":
    test_ollama()
