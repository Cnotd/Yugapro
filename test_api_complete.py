#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试完整的 API 端点 - 包括返回的 problems 和 suggestions"""

import requests
import json
import time
import cv2
import os
from pathlib import Path

API_BASE = "http://localhost:5000/api"

print("=" * 60)
print("完整 API 端点测试")
print("=" * 60)

# 测试 1: 获取可用动作
print("\n[测试 1] 获取可用动作...")
try:
    response = requests.get(f"{API_BASE}/pose/standards")
    poses = response.json()
    print(f"✓ 获取 {len(poses)} 个动作")
    pose_name = list(poses.keys())[0]
    print(f"  动作示例: {pose_name}")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

# 测试 2: 创建测试视频
print("\n[测试 2] 创建简单测试视频...")
try:
    video_path = "test_video.mp4"
    if not os.path.exists(video_path):
        # 创建一个简单的视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 30, (640, 480))
        
        for i in range(60):
            frame = (frame := 255 * (i % 2)) * (frame := 1)  # 简单闪烁
            blank = (255, 255, 255)
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img[:] = blank
            out.write(img)
        
        out.release()
        print("✓ 测试视频创建成功")
    else:
        print("✓ 使用现有测试视频")
except Exception as e:
    print(f"✗ 视频创建失败: {e}")
    # 尝试找一个现有的视频
    video_files = list(Path("uploads").glob("*.mp4"))
    if video_files:
        video_path = str(video_files[0])
        print(f"✓ 使用现有视频: {video_path}")
    else:
        print("✗ 没有可用的视频文件")
        exit(1)

# 测试 3: 上传视频并获取评估
print("\n[测试 3] 上传视频进行评估...")
try:
    with open(video_path, 'rb') as f:
        files = {'video': f}
        data = {'pose_name': '下犬式'}
        response = requests.post(f"{API_BASE}/assessment/upload", files=files, data=data)
        result = response.json()
        assessment_id = result.get('assessment_id')
        print(f"✓ 评估任务已创建: ID={assessment_id}")
except Exception as e:
    print(f"✗ 上传失败: {e}")
    exit(1)

# 测试 4: 轮询结果
print("\n[测试 4] 等待评估结果...")
try:
    for attempt in range(60):  # 最多等待60秒
        response = requests.get(f"{API_BASE}/assessment/{assessment_id}")
        result = response.json()
        status = result.get('status')
        
        if status == 'completed':
            print(f"✓ 评估完成!")
            break
        elif status == 'failed':
            print(f"✗ 评估失败: {result.get('error')}")
            exit(1)
        else:
            print(f"  状态: {status} ({attempt+1}/60)")
            time.sleep(1)
    else:
        print("✗ 评估超时")
        exit(1)
except Exception as e:
    print(f"✗ 等待结果失败: {e}")
    exit(1)

# 测试 5: 检查返回的数据
print("\n[测试 5] 验证返回的评估数据...")
try:
    assessment_data = result.get('result', {})
    
    # 检查分数
    total_score = assessment_data.get('total_score')
    print(f"✓ 总分: {total_score}")
    
    # 检查 problems
    problems = assessment_data.get('problems', [])
    print(f"✓ 问题数: {len(problems)}")
    if problems:
        for i, problem in enumerate(problems, 1):
            print(f"  问题 {i}: {problem[:50]}...")
    else:
        print("✗ 问题为空!")
    
    # 检查 suggestions
    suggestions = assessment_data.get('suggestions', [])
    print(f"✓ 建议数: {len(suggestions)}")
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  建议 {i}: {suggestion[:50]}...")
    else:
        print("✗ 建议为空!")
    
    # 完整数据输出
    print("\n完整返回数据:")
    print(json.dumps(assessment_data, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"✗ 数据验证失败: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✓ 所有测试通过!")
print("=" * 60)
