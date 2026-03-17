"""
可视化工具模块
提供数据可视化的函数
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import List, Dict, Optional, Tuple
import io
import base64

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def plot_score_breakdown(score: Dict, save_path: Optional[str] = None) -> Optional[str]:
    """
    绘制评分分解图
    
    Args:
        score: 分数字典 (total, accuracy, stability, coordination)
        save_path: 保存路径(可选)
        
    Returns:
        如果未保存,返回base64编码的图像字符串
    """
    labels = ['角度准确性', '动作稳定性', '整体协调性']
    sizes = [score['accuracy'], score['stability'], score['coordination']]
    max_values = [40, 30, 30]  # 各项满分
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(len(labels))
    
    bars = ax.bar(x_pos, sizes, color=colors, alpha=0.8)
    
    # 添加最大值参考线
    for i, max_val in enumerate(max_values):
        ax.axhline(y=max_val, color='gray', linestyle='--', alpha=0.3, xmin=i/len(labels), xmax=(i+1)/len(labels))
    
    # 在柱子上添加数值标签
    for i, (bar, max_val) in enumerate(zip(bars, max_values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
               f'{height}/{max_val}',
               ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('评估维度', fontsize=14, fontweight='bold')
    ax.set_ylabel('分数', fontsize=14, fontweight='bold')
    ax.set_title(f'瑜伽动作评分分解 (总分: {score["total"]}/100)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylim(0, 45)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return None
    else:
        # 转换为base64字符串
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        return img_base64


def plot_angle_over_time(angles_seq: List[Dict], 
                        angle_names: List[str],
                        save_path: Optional[str] = None) -> Optional[str]:
    """
    绘制角度随时间变化曲线
    
    Args:
        angles_seq: 角度序列
        angle_names: 要绘制的角度名称列表
        save_path: 保存路径(可选)
        
    Returns:
        如果未保存,返回base64编码的图像字符串
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    for idx, angle_name in enumerate(angle_names):
        values = []
        for angles in angles_seq:
            if angle_name in angles and angles[angle_name] is not None:
                values.append(angles[angle_name])
        
        if values:
            ax.plot(values, label=angle_name, linewidth=2, 
                   color=colors[idx % len(colors)], marker='o', 
                   markersize=4, alpha=0.8)
    
    ax.set_xlabel('帧数', fontsize=14, fontweight='bold')
    ax.set_ylabel('角度 (°)', fontsize=14, fontweight='bold')
    ax.set_title('关节角度随时间变化', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return None
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        return img_base64


def plot_angle_distribution(stats: Dict, 
                           save_path: Optional[str] = None) -> Optional[str]:
    """
    绘制角度分布图(均值±标准差)
    
    Args:
        stats: 统计特征字典
        save_path: 保存路径(可选)
        
    Returns:
        如果未保存,返回base64编码的图像字符串
    """
    if "mean" not in stats or "std" not in stats:
        return None
    
    angle_names = list(stats["mean"].keys())
    means = [stats["mean"][name] for name in angle_names]
    stds = [stats["std"][name] for name in angle_names]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x_pos = np.arange(len(angle_names))
    
    # 绘制误差条
    bars = ax.bar(x_pos, means, yerr=stds, 
                 color='#4ECDC4', alpha=0.8, 
                 capsize=5, error_kw={'linewidth': 2})
    
    # 添加数值标签
    for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + std + 2,
               f'{mean:.1f}±{std:.1f}°',
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('关节', fontsize=14, fontweight='bold')
    ax.set_ylabel('角度 (°)', fontsize=14, fontweight='bold')
    ax.set_title('各关节角度分布 (均值±标准差)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(angle_names, fontsize=11, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return None
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        return img_base64


def create_summary_dashboard(score: Dict,
                            problems: List[str],
                            suggestions: List[str],
                            save_path: Optional[str] = None) -> Optional[str]:
    """
    创建综合评估仪表板
    
    Args:
        score: 分数字典
        problems: 问题列表
        suggestions: 建议列表
        save_path: 保存路径(可选)
        
    Returns:
        如果未保存,返回base64编码的图像字符串
    """
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. 总分显示
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    ax1.text(0.5, 0.5, f'总分\n{score["total"]}/100',
            ha='center', va='center', fontsize=48, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#4ECDC4', alpha=0.8))
    ax1.set_title('综合评分', fontsize=16, fontweight='bold', pad=20)
    
    # 2. 分数分解饼图
    ax2 = fig.add_subplot(gs[0, 1])
    labels = ['角度准确性', '动作稳定性', '整体协调性']
    sizes = [score['accuracy'], score['stability'], score['coordination']]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax2.set_title('评分构成', fontsize=14, fontweight='bold')
    
    # 3. 主要问题
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.axis('off')
    problem_text = "主要问题:\n\n"
    for i, problem in enumerate(problems[:3], 1):
        problem_text += f"{i}. {problem}\n\n"
    ax3.text(0.1, 0.9, problem_text, ha='left', va='top', fontsize=11,
            bbox=dict(boxstyle='round', facecolor='#FFEAA7', alpha=0.6))
    ax3.set_title('发现问题', fontsize=14, fontweight='bold', pad=20)
    
    # 4. 改进建议
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    suggestion_text = "改进建议:\n\n"
    for i, suggestion in enumerate(suggestions[:3], 1):
        suggestion_text += f"{i}. {suggestion}\n\n"
    ax4.text(0.1, 0.9, suggestion_text, ha='left', va='top', fontsize=11,
            bbox=dict(boxstyle='round', facecolor='#96CEB4', alpha=0.6))
    ax4.set_title('改进建议', fontsize=14, fontweight='bold', pad=20)
    
    fig.suptitle('瑜伽动作评估报告', fontsize=18, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return None
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        return img_base64


def plot_landmarks_scatter(landmarks: List[Dict],
                          save_path: Optional[str] = None) -> Optional[str]:
    """
    绘制关键点散点图
    
    Args:
        landmarks: 关键点列表
        save_path: 保存路径(可选)
        
    Returns:
        如果未保存,返回base64编码的图像字符串
    """
    if not landmarks:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    x_coords = [lm["x"] for lm in landmarks]
    y_coords = [lm["y"] for lm in landmarks]
    visibilities = [lm["visibility"] for lm in landmarks]
    
    # 根据可见度设置透明度
    alphas = [v if v > 0.5 else 0.2 for v in visibilities]
    
    scatter = ax.scatter(x_coords, y_coords, c=range(len(landmarks)), 
                        cmap='viridis', s=100, alpha=0.8, edgecolors='black')
    
    # 添加关键点编号
    for i, (x, y) in enumerate(zip(x_coords, y_coords)):
        ax.annotate(str(i), (x, y), xytext=(5, 5), 
                   textcoords='offset points', fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    ax.invert_yaxis()  # 图像坐标系
    ax.set_xlabel('X坐标', fontsize=12)
    ax.set_ylabel('Y坐标', fontsize=12)
    ax.set_title('人体关键点分布', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return None
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()
        return img_base64
