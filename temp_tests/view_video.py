"""
视频查看器 - 使用 OpenCV 播放标注视频
"""

import cv2

def play_video(video_path: str):
    """
    播放视频文件
    
    Args:
        video_path: 视频文件路径
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return
    
    # 获取视频信息
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"视频信息:")
    print(f"  分辨率: {width}x{height}")
    print(f"  帧率: {fps} FPS")
    print(f"  总帧数: {total_frames}")
    print(f"  时长: {total_frames/fps:.2f}秒")
    print("\n控制:")
    print("  空格键: 暂停/播放")
    print("  ← →: 快进/快退")
    print("  q: 退出")
    print("=" * 60)
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # 调整窗口大小
        cv2.imshow('Video Player', frame)
        
        # 等待按键 (1/fps 秒 = 正常播放速度)
        key = cv2.waitKey(1000 // fps) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord(' '):
            # 暂停
            print("暂停 (按空格继续)")
            cv2.waitKey(0)
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n视频播放结束")

if __name__ == "__main__":
    video_path = "data/output_test.mp4"
    play_video(video_path)
