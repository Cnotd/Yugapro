"""
完整的端到端测试：视频上传 -> 评估 -> 获取结果
"""
import urllib.request
import json
import time
import os

print("=" * 70)
print("端到端测试：视频上传和评估")
print("=" * 70)

# 创建一个测试视频文件（随机字节）
test_video_path = "test_video.mp4"
if not os.path.exists(test_video_path):
    with open(test_video_path, "wb") as f:
        # 写入一些随机字节模拟视频文件
        f.write(b"ftypisom" + (b"\x00" * 1000))  # 模拟 MP4 头
    print(f"✓ 创建测试视频: {test_video_path} ({os.path.getsize(test_video_path)} bytes)")

# 步骤 1: 上传视频
print("\n[步骤 1/3] 上传视频")
print("-" * 70)

try:
    # 读取视频文件
    with open(test_video_path, "rb") as f:
        video_data = f.read()
    
    # 创建 multipart 表单数据
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="video"; filename="test.mp4"\r\n'
        "Content-Type: video/mp4\r\n\r\n"
    ).encode() + video_data + f"\r\n--{boundary}\r\n".encode() + (
        'Content-Disposition: form-data; name="pose_name"\r\n\r\n'
        "Mountain Pose\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    
    req = urllib.request.Request(
        "http://localhost:8080/api/assessment/upload",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        upload_result = json.loads(response.read().decode())
        assessment_id = upload_result.get("id")
        print(f"✓ 视频上传成功")
        print(f"  Assessment ID: {assessment_id}")
        print(f"  状态: {upload_result.get('status')}")
        print(f"  消息: {upload_result.get('message')}")
        
except Exception as e:
    print(f"✗ 上传失败: {e}")
    exit(1)

# 步骤 2: 检查评估状态
print("\n[步骤 2/3] 检查评估状态")
print("-" * 70)

try:
    url = f"http://localhost:8080/api/assessment/{assessment_id}"
    req = urllib.request.Request(url)
    
    with urllib.request.urlopen(req, timeout=5) as response:
        status_result = json.loads(response.read().decode())
        print(f"✓ 获取状态成功")
        print(f"  总评分: {status_result.get('total_score', 'N/A')}")
        print(f"  状态: {status_result.get('status')}")
        
except Exception as e:
    print(f"✗ 获取状态失败: {e}")
    exit(1)

# 步骤 3: 获取详细结果
print("\n[步骤 3/3] 获取详细评估结果")
print("-" * 70)

try:
    url = f"http://localhost:8080/api/assessment/{assessment_id}/result"
    req = urllib.request.Request(url)
    
    with urllib.request.urlopen(req, timeout=5) as response:
        result = json.loads(response.read().decode())
        print(f"✓ 获取详细结果成功")
        print(f"\n  总评分: {result.get('total_score', 'N/A'):.1f}/100")
        print(f"  姿态: {result.get('pose_name', 'Unknown')}")
        print(f"  状态: {result.get('status')}")
        print(f"\n  细项评分:")
        print(f"    - 结构分: {result.get('structure_score', 'N/A'):.1f}/60")
        print(f"    - 正位分: {result.get('alignment_score', 'N/A'):.1f}/30")
        print(f"    - 稳定分: {result.get('stability_score', 'N/A'):.1f}/10")
        
        problems = result.get('problems', [])
        if problems:
            print(f"\n  问题点 ({len(problems)}):")
            for p in problems:
                print(f"    • {p}")
        
        suggestions = result.get('suggestions', [])
        if suggestions:
            print(f"\n  改进建议 ({len(suggestions)}):")
            for s in suggestions:
                print(f"    • {s}")
        
except Exception as e:
    print(f"✗ 获取详细结果失败: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ 端到端测试成功！系统工作正常")
print("=" * 70)

# 清理测试文件
os.remove(test_video_path)
print(f"\n清理: 测试视频已删除")
