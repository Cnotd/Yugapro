"""
测试模型输出，查看实际返回内容
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ollama_client import OllamaClient
from src.prompt_builder import PromptBuilder

def test_model_output():
    print("=" * 60)
    print("测试模型输出格式")
    print("=" * 60)
    
    # 初始化
    client = OllamaClient()
    builder = PromptBuilder()
    
    # 模拟评估数据
    stats = {
        "mean": {
            "left_knee": 95.0,
            "right_knee": 92.0,
            "left_hip": 85.0,
            "right_hip": 88.0,
            "spine_angle": 3.0
        },
        "std": {
            "left_knee": 2.5,
            "right_knee": 3.0,
            "left_hip": 4.0,
            "right_hip": 3.5,
            "spine_angle": 1.0
        }
    }
    stability_score = 8.5
    
    # 构建提示词
    prompt = builder.build(stats, stability_score, "下犬式", {
        "angles": {
            "髋关节": (80, 100),
            "膝关节": (170, 180),
            "肩关节": (160, 180)
        },
        "common_errors": ["拱背", "弯膝", "耸肩"],
        "description": "身体呈倒V字形，双手和双脚撑地"
    })
    
    print("\n生成的提示词:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    
    # 调用模型
    print("\n调用模型...")
    try:
        response = client.generate(prompt)
        
        print("\n模型返回内容:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        
        # 保存到文件以便查看
        with open("model_output.txt", "w", encoding="utf-8") as f:
            f.write("提示词:\n")
            f.write(prompt)
            f.write("\n\n模型返回:\n")
            f.write(response)
        
        print("\n✓ 完整内容已保存到 model_output.txt")
        
    except Exception as e:
        print(f"✗ 调用失败: {e}")

if __name__ == "__main__":
    test_model_output()
