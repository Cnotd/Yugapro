# -*- coding: utf-8 -*-
"""
半月式完整评测脚本
整合角度检测和Ollama LLM评估
"""

import sys
import os
import json
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from config.settings import POSE_STANDARDS


def load_angle_data(angle_data_path: Path):
    """加载角度数据"""
    with open(angle_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 转换数据格式
    avg_angles = data['avg_angles']
    std_angles = data['std_angles']

    # 重命名键以匹配prompt builder的期望格式
    stats_mean = {}
    stats_std = {}

    # 映射关系
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

    # 计算稳定性评分（基于标准差）
    stability_scores = []
    for std_val in stats_std.values():
        # 标准差越小，稳定性越高
        if std_val < 5:
            stability_scores.append(1.0)
        elif std_val < 10:
            stability_scores.append(0.8)
        elif std_val < 15:
            stability_scores.append(0.6)
        else:
            stability_scores.append(0.4)

    stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.5

    return stats, stability


def main():
    print("\n" + "="*70)
    print(" "*20 + "半月式完整评测")
    print("="*70)

    # 数据路径
    video_dir = Path("data/archive/Ardhakati_Chakrasana/Ardhakati Chakrasana Right Step Angle 1")
    angle_data_path = video_dir / "angle_analysis" / "angle_data.json"

    if not angle_data_path.exists():
        print(f"\n错误: 角度数据文件不存在: {angle_data_path}")
        print("请先运行角度检测生成数据")
        return

    # 步骤1: 加载角度数据
    print("\n[步骤 1/5] 加载角度数据...")
    try:
        stats, stability = load_angle_data(angle_data_path)
        print(f"  角度数据加载成功")
        print(f"  平均角度数: {len(stats['mean'])}")
        print(f"  稳定性评分: {stability:.2f}")

        print(f"\n  平均角度详情:")
        for name, value in stats['mean'].items():
            print(f"    {name}: {value:.1f}°")

        print(f"\n  稳定性详情（标准差）:")
        for name, value in stats['std'].items():
            status = "稳定" if value < 5 else "一般" if value < 10 else "不稳定"
            print(f"    {name}: {value:.2f}° ({status})")

    except Exception as e:
        print(f"  错误: 加载数据失败 - {e}")
        return

    # 步骤2: 初始化模块
    print("\n[步骤 2/5] 初始化模块...")
    prompt_builder = PromptBuilder()
    ollama_client = OllamaClient()
    result_parser = ResultParser()
    print("  模块初始化完成")

    # 步骤3: 检查Ollama连接
    print("\n[步骤 3/5] 检查 Ollama 服务...")
    if not ollama_client.check_connection():
        print("  错误: Ollama 服务不可用")
        print("  请确保 Ollama 正在运行: ollama serve")
        return
    print("  Ollama 服务连接正常")

    # 步骤4: 构建提示词
    print("\n[步骤 4/5] 构建 AI 评估提示词...")
    pose_name = "半月式"
    pose_standard = POSE_STANDARDS.get(pose_name)

    if not pose_standard:
        print(f"  警告: 未找到 '{pose_name}' 的标准配置")
        print(f"  可用动作: {list(POSE_STANDARDS.keys())}")
        return

    prompt = prompt_builder.build(stats, stability, pose_name, pose_standard)
    print(f"  提示词构建完成 (长度: {len(prompt)} 字符)")

    # 步骤5: 调用模型
    print("\n[步骤 5/5] 调用 Ollama 模型进行评估...")
    print("  正在等待模型响应...")

    try:
        model_response = ollama_client.generate(prompt)
        print(f"  模型响应成功 (长度: {len(model_response)} 字符)")

        # 显示原始响应
        print("\n" + "="*70)
        print(" "*15 + "模型原始响应")
        print("="*70)
        print(model_response)
        print("="*70)

        # 解析结果
        print("\n正在解析评估结果...")
        assessment_result = result_parser.parse(model_response)

        if assessment_result.get('success', False):
            print("\n[成功] 评估结果解析成功!")
            result_data = assessment_result['data']
            score = result_data['score']

            print("\n" + "="*70)
            print(" "*20 + "半月式评估报告")
            print("="*70)

            # 评分
            print(f"\n总分: {score['total']}/100")
            print(f"{'─'*60}")
            print(f"角度准确性: {score['accuracy']}/40  分")
            print(f"动作稳定性: {score['stability']}/30  分")
            print(f"整体协调性: {score['coordination']}/30  分")

            # 评级
            if score['total'] >= 85:
                grade = "优秀"
            elif score['total'] >= 70:
                grade = "良好"
            elif score['total'] >= 60:
                grade = "及格"
            else:
                grade = "需要改进"

            print(f"\n综合评级: {grade}")

            # 问题
            if result_data['problems']:
                print(f"\n主要问题:")
                for i, prob in enumerate(result_data['problems'], 1):
                    print(f"  {i}. {prob}")
            else:
                print(f"\n主要问题: 无明显问题")

            # 建议
            if result_data['suggestions']:
                print(f"\n改进建议:")
                for i, sugg in enumerate(result_data['suggestions'], 1):
                    print(f"  {i}. {sugg}")
            else:
                print(f"\n改进建议: 保持当前状态")

            # 保存评估结果
            report_path = video_dir / "ollama_assessment.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "pose_name": pose_name,
                    "timestamp": str(pd_timestamp()),
                    "angle_data": {
                        "mean": stats['mean'],
                        "std": stats['std'],
                        "stability": stability
                    },
                    "assessment": result_data
                }, f, indent=2, ensure_ascii=False)

            print(f"\n评估结果已保存到: {report_path}")

            # 生成文本报告
            text_report_path = video_dir / "ollama_assessment_report.txt"
            with open(text_report_path, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write(" "*20 + "半月式AI评估报告\n")
                f.write("="*70 + "\n\n")

                f.write(f"动作名称: {pose_name}\n")
                f.write(f"综合评分: {score['total']}/100\n")
                f.write(f"评级: {grade}\n\n")

                f.write("分项得分:\n")
                f.write(f"  角度准确性: {score['accuracy']}/40\n")
                f.write(f"  动作稳定性: {score['stability']}/30\n")
                f.write(f"  整体协调性: {score['coordination']}/30\n\n")

                f.write("主要问题:\n")
                if result_data['problems']:
                    for i, prob in enumerate(result_data['problems'], 1):
                        f.write(f"  {i}. {prob}\n")
                else:
                    f.write("  无明显问题\n")

                f.write("\n改进建议:\n")
                if result_data['suggestions']:
                    for i, sugg in enumerate(result_data['suggestions'], 1):
                        f.write(f"  {i}. {sugg}\n")
                else:
                    f.write("  保持当前状态\n")

            print(f"文本报告已保存到: {text_report_path}")

            print("="*70)

        else:
            print("\n[警告] 无法解析模型响应")
            print(f"  错误: {assessment_result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"\n[错误] 模型调用失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print(" "*25 + "评测完成!")
    print("="*70 + "\n")


def pd_timestamp():
    """获取当前时间戳"""
    from datetime import datetime
    return datetime.now().isoformat()


if __name__ == "__main__":
    main()
