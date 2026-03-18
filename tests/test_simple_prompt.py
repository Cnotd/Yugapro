"""
简单提示词测试 - 验证 Ollama 能否正确输出 JSON
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ollama_client import OllamaClient


def test_simple_json():
    """测试简单 JSON 输出"""
    print("\n" + "="*70)
    print(" "*20 + "简单 JSON 测试")
    print("="*70)

    client = OllamaClient()

    simple_prompt = """请生成一个 JSON 对象,不要包含任何其他文字。

JSON 格式:
{
  "score": 85,
  "accuracy": 35,
  "stability": 25,
  "coordination": 25,
  "problems": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}

只返回 JSON,不要返回 markdown 格式,不要返回 ```json 标记。"""

    print("\n发送提示词...")
    print("-" * 60)
    print(simple_prompt)
    print("-" * 60)

    try:
        print("\n等待模型响应...")
        response = client.generate(simple_prompt)
        print(f"\n模型响应 (长度: {len(response)} 字符):")
        print("=" * 60)
        print(response)
        print("=" * 60)

        # 尝试解析
        import json
        try:
            data = json.loads(response.strip())
            print("\n[成功] JSON 解析成功!")
            print(f"分数: {data.get('score', 0)}")
            print(f"问题: {data.get('problems', [])}")
            print(f"建议: {data.get('suggestions', [])}")
        except json.JSONDecodeError as e:
            print(f"\n[失败] JSON 解析失败: {e}")

    except Exception as e:
        print(f"\n[错误] {str(e)}")

    print("\n" + "="*70)


if __name__ == "__main__":
    test_simple_json()
