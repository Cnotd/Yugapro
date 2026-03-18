"""
清晰提示词测试 - 使用更明确的指令
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ollama_client import OllamaClient


def test_clear_json():
    """测试清晰的 JSON 输出"""
    print("\n" + "="*70)
    print(" "*20 + "清晰指令测试")
    print("="*70)

    client = OllamaClient()

    clear_prompt = """You are a JSON API. Output only one valid JSON object, nothing else.

The JSON object must have this structure:
{
  "score": 85,
  "accuracy": 35,
  "stability": 25,
  "coordination": 25,
  "problems": ["Problem 1", "Problem 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}

Rules:
1. Output exactly one JSON object
2. No markdown code blocks (no ```json```)
3. No comments
4. No text before or after the JSON
5. The JSON must be valid

Now output the JSON:"""

    print("\n发送提示词...")
    print("-" * 60)
    print(clear_prompt[:200] + "...")
    print("-" * 60)

    try:
        print("\n等待模型响应...")
        response = client.generate(clear_prompt)
        print(f"\n模型响应 (长度: {len(response)} 字符):")
        print("=" * 60)
        print(response)
        print("=" * 60)

        # 尝试解析
        import json
        import re

        # 清理响应
        cleaned = response.strip()

        # 移除 markdown 标记
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)

        # 尝试提取第一个 JSON 对象
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            cleaned = match.group(0)

        print(f"\n清理后的 JSON:")
        print("-" * 60)
        print(cleaned)
        print("-" * 60)

        try:
            data = json.loads(cleaned)
            print("\n[成功] JSON 解析成功!")
            print(f"\n分数: {data.get('score', 0)}/100")
            print(f"  - 准确性: {data.get('accuracy', 0)}/40")
            print(f"  - 稳定性: {data.get('stability', 0)}/30")
            print(f"  - 协调性: {data.get('coordination', 0)}/30")
            print(f"\n问题:")
            for i, p in enumerate(data.get('problems', []), 1):
                print(f"  {i}. {p}")
            print(f"\n建议:")
            for i, s in enumerate(data.get('suggestions', []), 1):
                print(f"  {i}. {s}")
        except json.JSONDecodeError as e:
            print(f"\n[失败] JSON 解析失败: {e}")

    except Exception as e:
        print(f"\n[错误] {str(e)}")

    print("\n" + "="*70)


if __name__ == "__main__":
    test_clear_json()
