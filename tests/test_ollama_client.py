"""
Ollama客户端模块测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ollama_client import OllamaClient


def test_ollama_client():
    """测试Ollama客户端功能"""
    print("测试Ollama客户端模块...")
    
    client = OllamaClient()
    
    # 测试连接检查
    print("检查Ollama服务连接...")
    is_connected = client.check_connection()
    
    if is_connected:
        print("✓ Ollama服务连接成功")
        
        # 列出可用模型
        print("\n获取可用模型列表...")
        models = client.list_models()
        
        if models:
            print(f"✓ 找到 {len(models)} 个模型:")
            for model in models:
                print(f"  - {model.get('name', 'Unknown')}")
        else:
            print("⚠ 未找到可用模型")
        
        # 测试文本生成
        print("\n测试文本生成...")
        try:
            response = client.generate("Hello, say hi")
            print(f"✓ 文本生成成功: {response[:50]}...")
        except Exception as e:
            print(f"⚠ 文本生成测试失败: {e}")
    else:
        print("✗ 无法连接到Ollama服务")
        print("  请确保:")
        print("  1. Ollama已安装并运行")
        print("  2. 访问地址: http://localhost:11434")
    
    print("\nOllama客户端模块测试完成!")


if __name__ == "__main__":
    test_ollama_client()
