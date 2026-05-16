# -*- coding: utf-8 -*-
"""
测试qwen3.5:4b模型的集成
"""

import sys
import os
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ollama_client import OllamaClient
from src.prompt_builder import PromptBuilder
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS


def test_connection():
    """测试Ollama连接和模型"""
    print("\n" + "="*70)
    print(" "*20 + "测试 Ollama 连接")
    print("="*70)

    client = OllamaClient()

    # 1. 测试连接
    print("\n[1] 测试服务连接...")
    if not client.check_connection():
        print("  ✗ Ollama服务不可用")
        return False
    print("  ✓ Ollama服务连接正常")

    # 2. 列出可用模型
    print("\n[2] 列出可用模型...")
    models = client.list_models()
    if not models:
        print("  ✗ 未找到任何模型")
        return False

    print(f"  ✓ 找到 {len(models)} 个模型:")
    for model in models:
        name = model.get('name', 'unknown')
        print(f"    - {name}")

    # 3. 检查qwen3.5:4b是否存在
    print("\n[3] 检查 qwen3.5:4b 模型...")
    qwen_exists = any('qwen3.5' in model.get('name', '') for model in models)
    if not qwen_exists:
        print("  ✗ 未找到 qwen3.5:4b 模型")
        print("\n请先在Ollama中下载该模型:")
        print("  ollama pull qwen3.5:4b")
        return False
    print("  ✓ qwen3.5:4b 模型已安装")

    # 4. 获取当前模型信息
    print("\n[4] 获取模型信息...")
    model_info = client.get_model_info()
    if model_info:
        print("  当前配置模型:")
        print(f"    名称: {model_info.get('name', 'unknown')}")
        print(f"    大小: {model_info.get('size', 0) / (1024**3):.2f} GB")
        print(f"    修改时间: {model_info.get('modified_at', 'unknown')}")
    else:
        print("  无法获取模型信息")

    return True


def test_simple_generation():
    """测试简单的文本生成"""
    print("\n" + "="*70)
    print(" "*20 + "测试文本生成")
    print("="*70)

    client = OllamaClient()

    print("\n[1] 发送简单测试提示...")
    prompt = "请用一句话介绍什么是瑜伽。"

    try:
        response = client.generate(prompt)
        print(f"  模型响应: {response}")
        print("  ✓ 文本生成测试通过")
        return True
    except Exception as e:
        print(f"  ✗ 文本生成失败: {e}")
        return False


def test_json_generation():
    """测试JSON格式生成"""
    print("\n" + "="*70)
    print(" "*20 + "测试 JSON 生成")
    print("="*70)

    client = OllamaClient()

    print("\n[1] 请求JSON格式响应...")
    prompt = """请返回一个JSON对象，包含以下信息:
{
  "pose_name": "下犬式",
  "difficulty": "中等",
  "benefits": ["增强臂力", "拉伸脊柱", "改善循环"]
}

只返回JSON，不要任何其他文字。"""

    try:
        response = client.generate(prompt)
        print(f"  原始响应: {response}")

        # 解析JSON
        parser = ResultParser()
        result = parser.parse(response)

        if result.get('success'):
            print(f"  ✓ JSON解析成功")
            print(f"  解析结果: {result['data']}")
            return True
        else:
            print(f"  ✗ JSON解析失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"  ✗ 生成失败: {e}")
        return False


def test_pose_assessment():
    """测试完整的瑜伽动作评估"""
    print("\n" + "="*70)
    print(" "*20 + "测试瑜伽动作评估")
    print("="*70)

    # 准备测试数据
    test_stats = {
        'mean': {
            'left_elbow': 170.0,
            'right_elbow': 165.0,
            'left_knee': 172.0,
            'right_knee': 168.0,
            'left_hip': 90.0,
            'right_hip': 95.0,
            'left_shoulder': 175.0,
            'right_shoulder': 170.0
        },
        'std': {
            'left_elbow': 3.0,
            'right_elbow': 4.0,
            'left_knee': 2.0,
            'right_knee': 3.0,
            'left_hip': 5.0,
            'right_hip': 4.0,
            'left_shoulder': 2.5,
            'right_shoulder': 3.0
        }
    }
    test_stability = 0.85

    # 1. 构建提示词
    print("\n[1] 构建评估提示词...")
    prompt_builder = PromptBuilder()
    pose_name = "下犬式"
    pose_standard = POSE_STANDARDS.get(pose_name)

    if not pose_standard:
        print(f"  ✗ 未找到 '{pose_name}' 的标准配置")
        return False

    prompt = prompt_builder.build(test_stats, test_stability, pose_name, pose_standard)
    print(f"  ✓ 提示词构建完成 (长度: {len(prompt)} 字符)")

    # 2. 调用模型
    print("\n[2] 调用模型进行评估...")
    client = OllamaClient()

    try:
        response = client.generate(prompt)
        print(f"  ✓ 模型响应成功 (长度: {len(response)} 字符)")

        # 3. 解析结果
        print("\n[3] 解析评估结果...")
        parser = ResultParser()
        result = parser.parse(response)

        if result.get('success'):
            print("  ✓ 评估结果解析成功!")
            data = result['data']
            score = data['score']

            print("\n" + "-"*60)
            print("评估结果:")
            print(f"  总分: {score['total']}/100")
            print(f"  角度准确性: {score['accuracy']}/40")
            print(f"  动作稳定性: {score['stability']}/30")
            print(f"  整体协调性: {score['coordination']}/30")

            if data['problems']:
                print(f"\n  主要问题:")
                for i, prob in enumerate(data['problems'], 1):
                    print(f"    {i}. {prob}")

            if data['suggestions']:
                print(f"\n  改进建议:")
                for i, sugg in enumerate(data['suggestions'], 1):
                    print(f"    {i}. {sugg}")

            print("-"*60)
            return True
        else:
            print(f"  ✗ 解析失败: {result.get('error')}")
            print(f"\n  原始响应:\n{response}")
            return False

    except Exception as e:
        print(f"  ✗ 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_half_moon_assessment():
    """测试半月式评估"""
    print("\n" + "="*70)
    print(" "*20 + "测试半月式评估")
    print("="*70)

    import json

    # 加载半月式角度数据
    angle_data_path = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1/angle_analysis/angle_data.json")

    if not angle_data_path.exists():
        print(f"  ✗ 角度数据文件不存在: {angle_data_path}")
        return False

    print("\n[1] 加载角度数据...")
    with open(angle_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    avg_angles = data['avg_angles']
    std_angles = data['std_angles']

    # 转换数据格式
    stats_mean = {}
    stats_std = {}

    angle_mapping = {
        'left_elbow': 'left_elbow',
        'right_elbow': 'right_elbow',
        'left_knee': 'left_knee',
        'right_knee': 'right_knee',
        'left_hip': 'left_hip',
        'right_hip': 'right_hip',
        'left_shoulder': 'left_shoulder',
        'right_shoulder': 'right_shoulder'
    }

    for key, value in avg_angles.items():
        if key in angle_mapping:
            stats_mean[angle_mapping[key]] = value

    for key, value in std_angles.items():
        if key in angle_mapping:
            stats_std[angle_mapping[key]] = value

    stats = {
        'mean': stats_mean,
        'std': stats_std
    }

    # 计算稳定性
    stability_scores = []
    for std_val in stats_std.values():
        if std_val < 5:
            stability_scores.append(1.0)
        elif std_val < 10:
            stability_scores.append(0.8)
        elif std_val < 15:
            stability_scores.append(0.6)
        else:
            stability_scores.append(0.4)

    stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.5

    print(f"  ✓ 角度数据加载成功")
    print(f"  稳定性评分: {stability:.2f}")

    # 2. 构建提示词
    print("\n[2] 构建评估提示词...")
    prompt_builder = PromptBuilder()
    pose_name = "半月式"
    pose_standard = POSE_STANDARDS.get(pose_name)

    if not pose_standard:
        print(f"  ✗ 未找到 '{pose_name}' 的标准配置")
        return False

    prompt = prompt_builder.build(stats, stability, pose_name, pose_standard)
    print(f"  ✓ 提示词构建完成 (长度: {len(prompt)} 字符)")

    # 3. 调用模型
    print("\n[3] 调用模型进行评估...")
    client = OllamaClient()

    try:
        response = client.generate(prompt)
        print(f"  ✓ 模型响应成功 (长度: {len(response)} 字符)")

        # 4. 解析结果
        print("\n[4] 解析评估结果...")
        parser = ResultParser()
        result = parser.parse(response)

        if result.get('success'):
            print("  ✓ 评估结果解析成功!")
            data = result['data']
            score = data['score']

            print("\n" + "-"*60)
            print("半月式评估结果:")
            print(f"  总分: {score['total']}/100")
            print(f"  角度准确性: {score['accuracy']}/40")
            print(f"  动作稳定性: {score['stability']}/30")
            print(f"  整体协调性: {score['coordination']}/30")

            # 评级
            if score['total'] >= 85:
                grade = "优秀"
            elif score['total'] >= 70:
                grade = "良好"
            elif score['total'] >= 60:
                grade = "及格"
            else:
                grade = "需要改进"

            print(f"  综合评级: {grade}")

            if data['problems']:
                print(f"\n  主要问题:")
                for i, prob in enumerate(data['problems'], 1):
                    print(f"    {i}. {prob}")

            if data['suggestions']:
                print(f"\n  改进建议:")
                for i, sugg in enumerate(data['suggestions'], 1):
                    print(f"    {i}. {sugg}")

            print("-"*60)
            return True
        else:
            print(f"  ✗ 解析失败: {result.get('error')}")
            print(f"\n  原始响应:\n{response}")
            return False

    except Exception as e:
        print(f"  ✗ 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" "*15 + "qwen3.5:4b 模型集成测试")
    print("="*70)

    results = {}

    # 运行测试
    results['连接测试'] = test_connection()
    if not results['连接测试']:
        print("\n" + "="*70)
        print("连接测试失败，无法继续其他测试")
        print("="*70)
        return

    results['文本生成'] = test_simple_generation()
    results['JSON生成'] = test_json_generation()
    results['动作评估'] = test_pose_assessment()
    results['半月式评估'] = test_half_moon_assessment()

    # 汇总结果
    print("\n" + "="*70)
    print(" "*25 + "测试汇总")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！qwen3.5:4b 模型集成成功！")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败")

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
