"""
动作标准库配置文件
包含5个瑜伽动作的标准角度范围和常见错误
"""

POSE_STANDARDS = {
    "下犬式": {
        "angles": {
            "髋关节": (80, 100),
            "膝关节": (170, 180),
            "肩关节": (160, 180),
        },
        "common_errors": [
            "拱背",
            "弯膝",
            "耸肩"
        ],
        "description": "身体呈倒V字形，双手和双脚撑地"
    },
    "树式": {
        "angles": {
            "支撑腿膝关节": (175, 180),
            "抬髋关节": (70, 110),
            "脊柱角度": (0, 5),
        },
        "common_errors": [
            "晃动",
            "髋歪",
            "脚滑落"
        ],
        "description": "单腿站立，另一腿脚掌贴于支撑腿大腿内侧"
    },
    "战士一式": {
        "angles": {
            "前腿膝关节": (90, 100),
            "后腿膝关节": (170, 180),
            "髋关节": (0, 10),
        },
        "common_errors": [
            "膝盖超过脚尖",
            "后脚外翻",
            "髋不正位"
        ],
        "description": "前弓步，后腿伸直，手臂向上伸展"
    },
    "三角式": {
        "angles": {
            "侧屈角度": (45, 90),
            "脊柱延展": (0, 5),
            "后腿膝关节": (170, 180),
        },
        "common_errors": [
            "含胸",
            "膝盖锁死",
            "身体前倾"
        ],
        "description": "双腿分开，身体向一侧倾斜"
    },
    "猫牛式": {
        "angles": {
            "脊柱屈曲": (10, 30),
            "脊柱伸展": (10, 30),
        },
        "common_errors": [
            "动作脱节",
            "呼吸不配合",
            "肩部耸起"
        ],
        "description": "四点跪姿，配合呼吸进行脊柱屈伸"
    },
    "半月式": {
        "angles": {
            "支撑腿膝关节": (170, 180),
            "脊柱角度": (0, 20),
            "髋关节": (160, 180),
            "手臂伸展": (160, 180),
        },
        "common_errors": [
            "支撑腿弯曲",
            "髋部下沉",
            "脊柱未对齐",
            "手臂未伸展"
        ],
        "description": "单腿站立，另一腿向后伸展并与地面平行，手臂向上伸展形成平衡姿势"
    }
}

# 关键点映射
# MediaPipe Pose 33个关键点索引
LANDMARKS_MAPPING = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32
}

# 骨骼连接关系
POSE_CONNECTIONS = [
    (11, 12),  # 肩膀
    (11, 13), (13, 15),  # 左臂
    (12, 14), (14, 16),  # 右臂
    (11, 23), (12, 24),  # 躯干
    (23, 25), (25, 27),  # 左腿
    (24, 26), (26, 28),  # 右腿
    (27, 29), (28, 30),  # 脚踝到脚跟
    (29, 31), (30, 32),  # 脚跟到脚尖
    (0, 1), (1, 2), (2, 3), (2, 4),  # 面部
]

# 视频参数配置
VIDEO_CONFIG = {
    "max_size_mb": 100,
    "max_duration_sec": 120,
    "supported_formats": [".mp4", ".avi", ".mov"],
    "fps": 30,
}

# Ollama配置
OLLAMA_CONFIG = {
    "host": "http://localhost:11434",
    "model": "qwen3.5:4b",
    "timeout": 120,
    "temperature": 0.7,
}

# 评估参数
ASSESSMENT_CONFIG = {
    "stability_threshold": 0.05,  # 稳定性阈值
    "angle_tolerance": 5,  # 角度容差
    "min_frames": 10,  # 最小帧数
}
