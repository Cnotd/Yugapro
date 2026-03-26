# 数据库使用指南

## 目录
1. [数据库概述](#数据库概述)
2. [初始化数据库](#初始化数据库)
3. [基础操作](#基础操作)
4. [高级查询](#高级查询)
5. [统计分析](#统计分析)
6. [维护操作](#维护操作)
7. [API参考](#api参考)
8. [最佳实践](#最佳实践)

---

## 数据库概述

本系统使用SQLite数据库，包含以下10张核心表：

| 表名 | 用途 | 记录数(示例) |
|------|------|---------------|
| user | 用户信息 | 用户数 |
| assessment_record | 评估记录 | 评估次数 |
| pose_standard | 动作标准库 | 动作种类数 |
| video_data | 视频数据 | 视频上传数 |
| user_progress | 用户进步跟踪 | 用户×动作数 |
| system_log | 系统日志 | 日志条目数 |
| feedback | 用户反馈 | 反馈数量 |
| tag | 标签 | 标签总数 |
| assessment_tag | 评估标签关联 | 评估×标签数 |
| statistics | 统计数据 | 每日统计条目 |

### 数据库文件位置
```
d:\yuga_test\data\yoga_assessment.db
```

---

## 初始化数据库

### 方法1: 使用Python代码

```python
from src.database import DatabaseManager

# 初始化数据库
db = DatabaseManager(db_path="data/yoga_assessment.db")
```

### 方法2: 直接执行SQL

```bash
# 在命令行执行
sqlite3 data/yoga_assessment.db < database_schema.sql
```

### 初始化内容

数据库初始化时会自动创建：
- 10张数据表
- 所有必要的索引
- 3个视图
- 2个触发器
- 默认管理员账户（用户名: admin, 密码: admin123）
- 5个动作标准（下犬式、树式、战士一式、三角式、半月式）
- 12个初始标签

---

## 基础操作

### 1. 用户操作

#### 创建用户
```python
from src.database import DatabaseManager

db = DatabaseManager()

user_id = db.create_user(
    username="zhangsan",
    password="hashed_password",  # 注意:实际应用中应加密
    email="zhangsan@example.com",
    role="user"
)
print(f"用户创建成功, ID: {user_id}")
```

#### 获取用户信息
```python
# 根据ID获取
user = db.get_user_by_id(1)
print(user['username'], user['email'])

# 根据用户名获取
user = db.get_user_by_username("zhangsan")
```

#### 列出用户
```python
users = db.list_users(limit=10, offset=0)
for user in users:
    print(f"{user['username']} - {user['role']} - {user['created_at']}")
```

#### 更新最后登录时间
```python
db.update_user_last_login(user_id=1)
```

#### 删除用户
```python
deleted = db.delete_user(user_id=1)
print(f"删除结果: {deleted}")
```

### 2. 评估记录操作

#### 创建评估记录
```python
import json

assessment_data = {
    'user_id': 1,
    'video_name': 'yoga_practice_20250321.mp4',
    'video_path': '/data/videos/yoga_practice_20250321.mp4',
    'pose_name': '下犬式',
    'total_score': 85.5,
    'structure_score': 52.0,
    'alignment_score': 25.5,
    'stability_score': 8.0,
    'angle_data': {
        'left_knee': {'mean': 170.5, 'std': 3.2},
        'right_knee': {'mean': 168.2, 'std': 2.8}
    },
    'graph_data': {
        'num_nodes': 33,
        'num_edges': 48,
        'avg_visibility': 0.85
    },
    'stability_rating': 8.5,
    'problems': ['膝关节过度弯曲', '肩膀耸起'],
    'suggestions': ['放松肩膀下沉', '伸直膝关节'],
    'annotated_video_path': '/data/processed/yoga_practice_20250321_annotated.mp4',
    'video_duration': 30.0,
    'video_fps': 30.0,
    'video_resolution': '1920x1080',
    'frame_count': 900,
    'processing_time': 18.5,
    'model_used': 'qwen3.5:4b'
}

record_id = db.create_assessment_record(assessment_data)
print(f"评估记录创建成功, ID: {record_id}")
```

#### 获取评估记录
```python
# 根据ID获取
record = db.get_assessment_record(record_id=1)
print(f"总分: {record['total_score']}")
print(f"问题: {record['problems']}")
```

#### 获取用户的评估历史
```python
assessments = db.get_user_assessments(user_id=1, limit=20)
for record in assessments:
    print(f"{record['pose_name']}: {record['total_score']}分 - {record['assessment_time']}")
```

#### 搜索评估记录
```python
# 按动作搜索
records = db.get_assessments_by_pose(pose_name="下犬式", limit=10)

# 按分数范围搜索
records = db.search_assessments(
    user_id=1,
    pose_name="下犬式",
    min_score=80.0,
    max_score=100.0
)

# 混合搜索
records = db.search_assessments(
    pose_name="下犬式",
    min_score=70.0
)
```

### 3. 动作标准操作

#### 获取动作标准
```python
standard = db.get_pose_standard("下犬式")
print(f"髋关节范围: {standard['hip_min']}° - {standard['hip_max']}°")
print(f"常见错误: {standard['common_errors']}")
```

#### 列出所有动作标准
```python
# 获取所有动作
standards = db.list_pose_standards()

# 按类别筛选
balance_poses = db.list_pose_standards(category="平衡")

# 按难度筛选
advanced_poses = db.list_pose_standards(difficulty="高级")
```

#### 创建自定义动作标准
```python
custom_standard = {
    'pose_name': '侧板式',
    'pose_name_en': 'Side Plank',
    'category': '核心',
    'difficulty_level': '中级',
    'hip_min': 170,
    'hip_max': 180,
    'knee_min': 175,
    'knee_max': 180,
    'shoulder_min': 85,
    'shoulder_max': 95,
    'spine_min': 0,
    'spine_max': 10,
    'description': '侧板式是核心力量训练体式...',
    'benefits': '强化核心、提升平衡、稳定肩膀',
    'contraindications': '手腕、肩部受伤者慎练',
    'common_errors': ['髋部塌陷', '肩膀耸起', '身体不在一条直线'],
    'suggestion_templates': [
        '保持核心收紧',
        '肩膀远离耳朵',
        '身体呈一条直线'
    ],
    'is_active': True
}

standard_id = db.create_pose_standard(custom_standard)
```

#### 更新动作标准
```python
update_data = {
    'common_errors': ['髋部塌陷', '肩膀耸起', '身体不在一条直线', '膝盖弯曲']
}
success = db.update_pose_standard("侧板式", update_data)
```

#### 删除动作标准(软删除)
```python
db.delete_pose_standard("侧板式")  # 只是标记为不活跃
```

### 4. 视频数据操作

#### 创建视频记录
```python
video_data = {
    'user_id': 1,
    'video_name': 'practice_video',
    'original_filename': 'IMG_0001.mp4',
    'file_path': '/data/videos/IMG_0001.mp4',
    'file_size': 10485760,  # 10MB
    'file_format': 'mp4',
    'video_duration': 30.0,
    'video_fps': 30.0,
    'video_width': 1920,
    'video_height': 1080,
    'upload_ip': '192.168.1.100'
}

video_id = db.create_video_record(video_data)
```

#### 更新视频处理状态
```python
# 标记为处理中
db.update_video_status(video_id=1, status='processing')

# 标记为完成
db.update_video_status(
    video_id=1,
    status='completed',
    assessment_record_id=5
)

# 标记为失败
db.update_video_status(
    video_id=1,
    status='failed',
    error='视频格式不支持'
)
```

### 5. 用户进步跟踪

#### 获取用户进步记录
```python
# 获取指定动作的进步记录
progress = db.get_user_progress(user_id=1, pose_name="下犬式")
if progress:
    print(f"评估次数: {progress['total_assessments']}")
    print(f"平均分: {progress['average_score']:.1f}")
    print(f"最高分: {progress['best_score']}")
    print(f"最低分: {progress['worst_score']}")

# 获取用户所有动作的进步记录
all_progress = db.get_user_progress(user_id=1)
for p in all_progress:
    print(f"{p['pose_name']}: {p['total_assessments']}次, 平均{p['average_score']:.1f}分")
```

**注意**: 用户进步记录会通过触发器自动更新,无需手动创建。

---

## 高级查询

### 1. 使用视图

#### 获取用户评估统计
```python
# 直接查询视图
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM view_user_assessment_stats
        WHERE user_id = 1
    """)
    stats = dict(cursor.fetchone())
    print(f"总评估: {stats['total_assessments']}")
    print(f"平均分: {stats['avg_score']:.1f}")
    print(f"动作种类: {stats['pose_types_count']}")
```

#### 获取动作评估统计
```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM view_pose_assessment_stats
        ORDER BY total_assessments DESC
    """)
    for row in cursor.fetchall():
        stats = dict(row)
        print(f"{stats['pose_name']}: {stats['total_assessments']}次评估, "
              f"平均分{stats['avg_score']:.1f}, 用户数{stats['user_count']}")
```

#### 获取每日统计
```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM view_daily_stats
        ORDER BY stat_date DESC
        LIMIT 30
    """)
    for row in cursor.fetchall():
        stats = dict(row)
        print(f"{stats['stat_date']}: {stats['total_assessments']}次评估, "
              f"平均{stats['avg_score']:.1f}分")
```

### 2. 标签操作

#### 创建标签
```python
tag_id = db.create_tag(
    tag_name="稳定",
    tag_type="quality",
    description="动作稳定,晃动小"
)
```

#### 为评估添加标签
```python
db.add_tag_to_assessment(assessment_id=1, tag_id=1)
```

#### 获取评估的标签
```python
tags = db.get_assessment_tags(assessment_id=1)
for tag in tags:
    print(f"{tag['tag_name']} ({tag['tag_type']})")
```

#### 列出所有标签
```python
# 所有标签
all_tags = db.get_tags()

# 按类型筛选
quality_tags = db.get_tags(tag_type="quality")
level_tags = db.get_tags(tag_type="level")
```

### 3. 日志操作

#### 添加日志
```python
db.add_log(
    log_type="assessment",
    log_level="INFO",
    action="create_assessment",
    message="创建评估记录",
    user_id=1,
    details=f"评估ID: {record_id}",
    ip_address="192.168.1.100"
)
```

#### 查询日志
```python
# 所有日志
logs = db.get_logs(limit=100)

# 按类型筛选
error_logs = db.get_logs(log_level="ERROR")

# 按用户筛选
user_logs = db.get_logs(user_id=1)

# 组合筛选
recent_errors = db.get_logs(
    log_level="ERROR",
    user_id=1,
    limit=50
)
```

### 4. 反馈操作

#### 创建反馈
```python
feedback_id = db.create_feedback({
    'user_id': 1,
    'assessment_record_id': 5,
    'feedback_type': 'suggestion',
    'rating': 5,
    'comment': '系统评估很准确,建议!'
})
```

#### 查询反馈
```python
# 所有反馈
all_feedbacks = db.get_feedbacks()

# 未解决的反馈
pending_feedbacks = db.get_feedbacks(is_resolved=False)

# 按类型筛选
bug_reports = db.get_feedbacks(feedback_type='bug')
```

---

## 统计分析

### 1. 系统总览
```python
stats = db.get_system_overview()
print(f"""
系统总览:
- 总用户数: {stats['total_users']}
- 总评估数: {stats['total_assessments']}
- 今日评估: {stats['today_assessments']}
- 平均分数: {stats['average_score']}
- 动作种类: {stats['pose_types']}
- 活跃用户(7天): {stats['active_users']}
""")
```

### 2. 用户统计
```python
user_stats = db.get_user_stats(user_id=1)
print(f"""
用户统计:
- 总评估: {user_stats['total_assessments']}
- 平均分: {user_stats['avg_score']:.1f}
- 最高分: {user_stats['max_score']}
- 最低分: {user_stats['min_score']}
- 动作种类: {user_stats['pose_types_count']}
- 首次评估: {user_stats['first_assessment']}
- 最近评估: {user_stats['last_assessment']}
""")
```

### 3. 动作统计
```python
# 所有动作统计
pose_stats = db.get_pose_stats()
for stat in pose_stats:
    print(f"{stat['pose_name']} ({stat['difficulty_level']}): "
          f"{stat['total_assessments']}次, 平均{stat['avg_score']:.1f}分, "
          f"{stat['user_count']}位用户")

# 单个动作统计
dog_stats = db.get_pose_stats(pose_name="下犬式")
print(f"下犬式: {dog_stats[0]['total_assessments']}次评估")
```

### 4. 每日统计
```python
daily_stats = db.get_daily_stats(days=30)
for stat in daily_stats:
    print(f"{stat['stat_date']}: "
          f"{stat['total_assessments']}次, "
          f"{stat['unique_users']}人, "
          f"平均{stat['avg_score']:.1f}分")
```

---

## 维护操作

### 1. 清理旧日志
```python
# 清理90天前的日志
deleted_count = db.cleanup_old_logs(days=90)
print(f"删除了 {deleted_count} 条旧日志")
```

### 2. 清理未处理的视频
```python
# 清理7天前仍未处理的视频
deleted_count = db.cleanup_pending_videos(days=7)
print(f"删除了 {deleted_count} 条未处理的视频记录")
```

### 3. 优化数据库
```python
db.optimize_database()
```

### 4. 数据备份
```python
import shutil
from datetime import datetime

# 备份数据库
backup_path = f"backup/yoga_assessment_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
Path("backup").mkdir(exist_ok=True)
shutil.copy2("data/yoga_assessment.db", backup_path)
print(f"数据库已备份到: {backup_path}")
```

---

## API参考

### DatabaseManager类

#### 初始化
```python
DatabaseManager(db_path: str = "data/yoga_assessment.db")
```

#### 用户相关
```python
create_user(username, password, email=None, role='user') -> int
get_user_by_id(user_id) -> Optional[Dict]
get_user_by_username(username) -> Optional[Dict]
update_user_last_login(user_id)
list_users(limit=100, offset=0) -> List[Dict]
delete_user(user_id) -> bool
```

#### 评估记录相关
```python
create_assessment_record(record_data) -> int
get_assessment_record(record_id) -> Optional[Dict]
get_user_assessments(user_id, limit=50, offset=0) -> List[Dict]
get_assessments_by_pose(pose_name, limit=50) -> List[Dict]
search_assessments(user_id=None, pose_name=None, min_score=None, max_score=None, limit=50) -> List[Dict]
```

#### 动作标准相关
```python
create_pose_standard(standard_data) -> int
get_pose_standard(pose_name) -> Optional[Dict]
list_pose_standards(category=None, difficulty=None) -> List[Dict]
update_pose_standard(pose_name, update_data) -> bool
delete_pose_standard(pose_name) -> bool
```

#### 视频数据相关
```python
create_video_record(video_data) -> int
update_video_status(video_id, status, error=None, assessment_record_id=None)
```

#### 用户进步相关
```python
get_user_progress(user_id, pose_name=None) -> Optional[Dict] | List[Dict]
```

#### 统计相关
```python
get_user_stats(user_id) -> Dict
get_pose_stats(pose_name=None) -> List[Dict]
get_daily_stats(days=30) -> List[Dict]
get_system_overview() -> Dict
```

#### 日志相关
```python
add_log(log_type, log_level, action, message, user_id=None, details=None, ip_address=None)
get_logs(log_type=None, log_level=None, user_id=None, limit=100) -> List[Dict]
```

#### 反馈相关
```python
create_feedback(feedback_data) -> int
get_feedbacks(feedback_type=None, is_resolved=None, limit=50) -> List[Dict]
```

#### 标签相关
```python
create_tag(tag_name, tag_type, description=None) -> int
get_tags(tag_type=None) -> List[Dict]
add_tag_to_assessment(assessment_id, tag_id)
get_assessment_tags(assessment_id) -> List[Dict]
```

#### 维护相关
```python
cleanup_old_logs(days=90) -> int
cleanup_pending_videos(days=7) -> int
optimize_database()
```

---

## 最佳实践

### 1. 密码安全
```python
import hashlib

def hash_password(password):
    """密码哈希(示例,实际应使用更安全的算法)"""
    return hashlib.sha256(password.encode()).hexdigest()

# 创建用户时
user_id = db.create_user(
    username="user1",
    password=hash_password("password123"),  # 存储哈希值
    email="user1@example.com"
)

# 验证密码时
user = db.get_user_by_username("user1")
if user and user['password'] == hash_password(input_password):
    print("密码正确")
```

### 2. JSON数据处理
```python
# JSON字段会自动解析
record = db.get_assessment_record(1)
print(record['angle_data']['left_knee']['mean'])  # 直接使用

# 创建记录时直接传递Python对象
assessment_data = {
    'angle_data': {'left_knee': 170.5, 'right_knee': 168.2},
    'problems': ['问题1', '问题2'],
    # ... 其他字段
}
db.create_assessment_record(assessment_data)
```

### 3. 批量操作
```python
# 使用事务批量插入
with db.get_connection() as conn:
    cursor = conn.cursor()
    for i in range(10):
        cursor.execute("""
            INSERT INTO system_log (log_type, log_level, action, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ('test', 'INFO', f'action_{i}', f'message_{i}', datetime.now()))
    conn.commit()
```

### 4. 错误处理
```python
try:
    user_id = db.create_user(...)
except Exception as e:
    print(f"创建用户失败: {e}")
    # 处理错误
```

### 5. 性能优化
```python
# 使用限制和分页
users = db.list_users(limit=100, offset=0)

# 使用索引字段查询
user = db.get_user_by_username("user1")  # username有索引

# 避免全表扫描
records = db.search_assessments(
    user_id=1,  # user_id有索引
    min_score=80.0
)
```

### 6. 数据备份
```python
import shutil
from datetime import datetime

def backup_database():
    """定期备份数据库"""
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"yoga_assessment_backup_{timestamp}.db"

    shutil.copy2("data/yoga_assessment.db", backup_path)
    print(f"数据库已备份: {backup_path}")

# 建议每天执行一次
backup_database()
```

---

## 常见问题

### Q1: 如何重置数据库?
```python
import os

# 删除现有数据库
if os.path.exists("data/yoga_assessment.db"):
    os.remove("data/yoga_assessment.db")

# 重新初始化
db = DatabaseManager()
```

### Q2: 如何导出数据?
```python
import json
import csv

# 导出为JSON
users = db.list_users()
with open('users.json', 'w', encoding='utf-8') as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

# 导出为CSV
assessments = db.get_user_assessments(user_id=1)
with open('assessments.csv', 'w', newline='', encoding='utf-8') as f:
    if assessments:
        writer = csv.DictWriter(f, fieldnames=assessments[0].keys())
        writer.writeheader()
        writer.writerows(assessments)
```

### Q3: 如何处理并发访问?
```python
# SQLite会自动处理并发写入
# 对于大量写入操作,建议使用事务
with db.get_connection() as conn:
    cursor = conn.cursor()
    # 批量操作
    conn.commit()
```

### Q4: 如何扩展数据库?
```python
# 添加新表
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY,
            field1 VARCHAR(100),
            field2 INTEGER
        )
    """)

# 添加新列
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE user ADD COLUMN new_field VARCHAR(100)
    """)
```

---

**文档版本**: 1.0
**最后更新**: 2026-03-21
