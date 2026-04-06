#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证 result_parser 是否正确处理 Qwen 格式"""

import json
from src.result_parser import ResultParser

parser = ResultParser()

# 模拟 Qwen API 返回的响应
qwen_response = """```json
{
    "total_score": 85,
    "structure_score": 50,
    "alignment_score": 25,
    "stability_score": 10,
    "problems": ["髋关节角度略偏高，可能导致骨盆前倾", "脊柱角度轻微弯曲，可能影响姿势的直线性"],
    "suggestions": ["调整骨盆位置，确保髋部与肩部对齐", "加强核心肌群控制，保持脊柱中立位"]
}
```"""

print("=" * 60)
print("测试 Result Parser - Qwen 格式")
print("=" * 60)

print("\n[输入] Qwen API 返回:")
print(qwen_response[:200] + "...")

print("\n[处理] 解析响应...")
result = parser.parse(qwen_response)

print(f"\n[输出] 解析结果:")
print(f"  Success: {result.get('success')}")
print(f"  Error: {result.get('error')}")

if result.get('success'):
    data = result.get('data', {})
    print(f"\n[分数数据]:")
    print(f"  Total: {data.get('score', {}).get('total')}")
    print(f"  Accuracy: {data.get('score', {}).get('accuracy')}")
    print(f"  Stability: {data.get('score', {}).get('stability')}")
    print(f"  Coordination: {data.get('score', {}).get('coordination')}")
    
    print(f"\n[问题]:")
    problems = data.get('problems', [])
    for i, p in enumerate(problems, 1):
        print(f"  {i}. {p}")
    
    print(f"\n[建议]:")
    suggestions = data.get('suggestions', [])
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s}")
    
    print("\n✓ 解析成功!")
else:
    print("\n✗ 解析失败!")

print("\n完整JSON结果:")
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "=" * 60)
