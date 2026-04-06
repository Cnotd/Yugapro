-- ================================================================
-- 瑜伽动作智能评估系统 - 数据库设计
-- ================================================================
-- 数据库类型: SQLite
-- 创建时间: 2026-03-21
-- 版本: 1.0

-- ================================================================
-- 1. 用户表 (user)
-- ================================================================
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    avatar_url VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    last_login DATETIME,
    is_active BOOLEAN DEFAULT 1,
    CONSTRAINT chk_role CHECK (role IN ('user', 'admin'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);
CREATE INDEX IF NOT EXISTS idx_user_created_at ON user(created_at);

-- ================================================================
-- 2. 评估记录表 (assessment_record)
-- ================================================================
CREATE TABLE IF NOT EXISTS assessment_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_name VARCHAR(255) NOT NULL,
    video_path VARCHAR(500) NOT NULL,
    pose_name VARCHAR(50) NOT NULL,
    assessment_time DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    total_score FLOAT,
    structure_score FLOAT,
    alignment_score FLOAT,
    stability_score FLOAT,

    -- 角度数据 (JSON格式存储)
    angle_data TEXT,

    -- 姿态图数据 (JSON格式存储)
    graph_data TEXT,

    -- 稳定性评分
    stability_rating FLOAT,

    -- 问题和建议 (JSON格式)
    problems TEXT,
    suggestions TEXT,

    -- 标注视频路径
    annotated_video_path VARCHAR(500),

    -- 视频信息
    video_duration FLOAT,
    video_fps FLOAT,
    video_resolution VARCHAR(50),
    frame_count INTEGER,

    -- 处理信息
    processing_time FLOAT,
    model_used VARCHAR(50),

    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_assessment_user_id ON assessment_record(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_pose_name ON assessment_record(pose_name);
CREATE INDEX IF NOT EXISTS idx_assessment_time ON assessment_record(assessment_time);
CREATE INDEX IF NOT EXISTS idx_assessment_score ON assessment_record(total_score);

-- ================================================================
-- 3. 动作标准表 (pose_standard)
-- ================================================================
CREATE TABLE IF NOT EXISTS pose_standard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pose_name VARCHAR(50) NOT NULL UNIQUE,
    pose_name_en VARCHAR(50),
    category VARCHAR(50),
    difficulty_level VARCHAR(20),

    -- 标准角度范围
    hip_min FLOAT,
    hip_max FLOAT,
    knee_min FLOAT,
    knee_max FLOAT,
    shoulder_min FLOAT,
    shoulder_max FLOAT,
    spine_min FLOAT,
    spine_max FLOAT,

    -- 动作描述
    description TEXT,
    benefits TEXT,
    contraindications TEXT,

    -- 常见错误 (JSON格式)
    common_errors TEXT,

    -- 改进建议模板 (JSON格式)
    suggestion_templates TEXT,

    -- 状态
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),

    CONSTRAINT chk_difficulty CHECK (difficulty_level IN ('初级', '中级', '高级'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_pose_name ON pose_standard(pose_name);
CREATE INDEX IF NOT EXISTS idx_pose_category ON pose_standard(category);
CREATE INDEX IF NOT EXISTS idx_pose_difficulty ON pose_standard(difficulty_level);

-- ================================================================
-- 4. 视频数据表 (video_data)
-- ================================================================
CREATE TABLE IF NOT EXISTS video_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_format VARCHAR(20),
    video_duration FLOAT,
    video_fps FLOAT,
    video_width INTEGER,
    video_height INTEGER,

    -- 上传信息
    upload_time DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    upload_ip VARCHAR(50),

    -- 处理状态
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_start_time DATETIME,
    processing_end_time DATETIME,
    processing_error TEXT,

    -- 关联的评估记录
    assessment_record_id INTEGER,

    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (assessment_record_id) REFERENCES assessment_record(id) ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_video_user_id ON video_data(user_id);
CREATE INDEX IF NOT EXISTS idx_video_upload_time ON video_data(upload_time);
CREATE INDEX IF NOT EXISTS idx_video_status ON video_data(processing_status);

-- ================================================================
-- 5. 用户进步记录表 (user_progress)
-- ================================================================
CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pose_name VARCHAR(50) NOT NULL,

    -- 进度统计
    total_assessments INTEGER DEFAULT 0,
    average_score FLOAT,
    best_score FLOAT,
    worst_score FLOAT,
    latest_score FLOAT,

    -- 改进趋势
    improvement_trend TEXT,  -- JSON: [{"date": "2026-03-20", "score": 85}, ...]

    -- 成就
    achievements TEXT,  -- JSON: ["首次评估", "满分动作", ...]

    -- 更新时间
    first_assessment_time DATETIME,
    last_assessment_time DATETIME,
    updated_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    UNIQUE(user_id, pose_name)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_progress_user_pose ON user_progress(user_id, pose_name);
CREATE INDEX IF NOT EXISTS idx_progress_avg_score ON user_progress(average_score);

-- ================================================================
-- 6. 系统日志表 (system_log)
-- ================================================================
CREATE TABLE IF NOT EXISTS system_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    log_type VARCHAR(20) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    action VARCHAR(100),
    message TEXT,
    details TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),

    CONSTRAINT chk_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_log_user_id ON system_log(user_id);
CREATE INDEX IF NOT EXISTS idx_log_type ON system_log(log_type);
CREATE INDEX IF NOT EXISTS idx_log_level ON system_log(log_level);
CREATE INDEX IF NOT EXISTS idx_log_created_at ON system_log(created_at);

-- ================================================================
-- 7. 反馈与建议表 (feedback)
-- ================================================================
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    assessment_record_id INTEGER,
    feedback_type VARCHAR(20) NOT NULL,
    rating INTEGER,
    comment TEXT,
    is_resolved BOOLEAN DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    resolved_at DATETIME,

    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (assessment_record_id) REFERENCES assessment_record(id) ON DELETE SET NULL,

    CONSTRAINT chk_feedback_type CHECK (feedback_type IN ('bug', 'suggestion', 'complaint', 'other')),
    CONSTRAINT chk_rating CHECK (rating >= 1 AND rating <= 5)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_resolved ON feedback(is_resolved);

-- ================================================================
-- 8. 标签表 (tag)
-- ================================================================
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name VARCHAR(50) NOT NULL UNIQUE,
    tag_type VARCHAR(20) NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tag_name ON tag(tag_name);
CREATE INDEX IF NOT EXISTS idx_tag_type ON tag(tag_type);

-- ================================================================
-- 9. 评估记录标签关联表 (assessment_tag)
-- ================================================================
CREATE TABLE IF NOT EXISTS assessment_tag (
    assessment_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (assessment_id, tag_id),
    FOREIGN KEY (assessment_id) REFERENCES assessment_record(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- ================================================================
-- 10. 统计数据表 (statistics)
-- ================================================================
CREATE TABLE IF NOT EXISTS statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    stat_key VARCHAR(50) NOT NULL,
    stat_value INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(stat_date, stat_type, stat_key)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stat_date ON statistics(stat_date);
CREATE INDEX IF NOT EXISTS idx_stat_type ON statistics(stat_type);
CREATE INDEX IF NOT EXISTS idx_stat_date_type_key ON statistics(stat_date, stat_type, stat_key);

-- ================================================================
-- 初始化数据
-- ================================================================

-- 插入默认管理员账户
INSERT OR IGNORE INTO user (username, password, email, role, created_at)
VALUES ('admin', 'admin123', 'admin@yoga.com', 'admin', datetime('now', 'localtime'));

-- 插入动作标准数据
INSERT OR IGNORE INTO pose_standard (pose_name, pose_name_en, category, difficulty_level,
    hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max,
    description, common_errors)
VALUES
(
    '下犬式',
    'Downward Facing Dog',
    '倒立',
    '初级',
    160, 175, 165, 180, 80, 100, 0, 10,
    '下犬式是瑜伽中最基础的体式之一，能够拉伸脊柱、强化手臂和肩膀、平静大脑。',
    '["膝关节过度弯曲", "肩膀耸起", "脊柱塌陷或弓起", "脚跟未着地"]'
);

INSERT OR IGNORE INTO pose_standard (pose_name, pose_name_en, category, difficulty_level,
    hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max,
    description, common_errors)
VALUES
(
    '树式',
    'Tree Pose',
    '平衡',
    '初级',
    160, 170, 175, 180, 85, 95, 0, 5,
    '树式是瑜伽中的基础平衡体式，能够提高专注力、增强腿部力量、改善身体平衡。',
    '["支撑腿膝盖内扣", "髋部侧倾", "肩膀紧张耸起", "脚掌未贴紧大腿"]'
);

INSERT OR IGNORE INTO pose_standard (pose_name, pose_name_en, category, difficulty_level,
    hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max,
    description, common_errors)
VALUES
(
    '战士一式',
    'Warrior I',
    '站立体式',
    '中级',
    150, 165, 85, 95, 75, 90, 0, 10,
    '战士一式是力量型体式，能够强化腿部和核心、打开胸部、提升专注力。',
    '["前膝内扣", "髋部不正", "胸部未打开", "后脚跟未着地"]'
);

INSERT OR IGNORE INTO pose_standard (pose_name, pose_name_en, category, difficulty_level,
    hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max,
    description, common_errors)
VALUES
(
    '三角式',
    'Triangle Pose',
    '站立体式',
    '中级',
    80, 95, 165, 180, 90, 105, 0, 15,
    '三角式是经典的侧展体式，能够拉伸侧身、强化腿部、打开髋部。',
    '["膝关节锁死", "脊柱过度扭转", "肩膀耸起", "胸部向前塌陷"]'
);

INSERT OR IGNORE INTO pose_standard (pose_name, pose_name_en, category, difficulty_level,
    hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max,
    description, common_errors)
VALUES
(
    '半月式',
    'Half Moon Pose',
    '平衡',
    '中级',
    155, 170, 165, 175, 60, 80, 0, 15,
    '半月式是挑战性平衡体式，能够增强核心力量、打开髋部、提升平衡能力。',
    '["脊柱侧弯", "膝关节弯曲", "手臂位置不正确", "支撑脚未用力"]'
);

-- 插入初始标签数据
INSERT OR IGNORE INTO tag (tag_name, tag_type, description) VALUES
('稳定', 'quality', '动作稳定，晃动小'),
('需要改进', 'quality', '动作有待提升'),
('优秀', 'quality', '动作标准，表现优秀'),
('初级', 'level', '适合初学者'),
('中级', 'level', '适合有一定基础的练习者'),
('高级', 'level', '适合资深练习者'),
('力量型', 'style', '需要较强力量'),
('柔韧型', 'style', '需要较好柔韧性'),
('平衡型', 'style', '需要较好平衡能力'),
('倒立', 'category', '倒立类体式'),
('平衡', 'category', '平衡类体式'),
('站立体式', 'category', '站立体式');

-- ================================================================
-- 创建视图
-- ================================================================

-- 用户评估统计视图
CREATE VIEW IF NOT EXISTS view_user_assessment_stats AS
SELECT
    u.id AS user_id,
    u.username,
    COUNT(ar.id) AS total_assessments,
    AVG(ar.total_score) AS avg_score,
    MAX(ar.total_score) AS max_score,
    MIN(ar.total_score) AS min_score,
    COUNT(DISTINCT ar.pose_name) AS pose_types_count,
    MIN(ar.assessment_time) AS first_assessment,
    MAX(ar.assessment_time) AS last_assessment
FROM user u
LEFT JOIN assessment_record ar ON u.id = ar.user_id
GROUP BY u.id, u.username;

-- 动作评估统计视图
CREATE VIEW IF NOT EXISTS view_pose_assessment_stats AS
SELECT
    ps.id AS pose_id,
    ps.pose_name,
    ps.difficulty_level,
    COUNT(ar.id) AS total_assessments,
    AVG(ar.total_score) AS avg_score,
    MAX(ar.total_score) AS max_score,
    MIN(ar.total_score) AS min_score,
    COUNT(DISTINCT ar.user_id) AS user_count
FROM pose_standard ps
LEFT JOIN assessment_record ar ON ps.pose_name = ar.pose_name
GROUP BY ps.id, ps.pose_name, ps.difficulty_level;

-- 每日统计视图
CREATE VIEW IF NOT EXISTS view_daily_stats AS
SELECT
    DATE(assessment_time) AS stat_date,
    COUNT(*) AS total_assessments,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(total_score) AS avg_score,
    AVG(processing_time) AS avg_processing_time
FROM assessment_record
GROUP BY DATE(assessment_time);

-- ================================================================
-- 创建触发器
-- ================================================================

-- 更新用户进步记录触发器
DROP TRIGGER IF EXISTS trigger_update_user_progress;
CREATE TRIGGER trigger_update_user_progress
AFTER INSERT ON assessment_record
WHEN NEW.total_score IS NOT NULL
BEGIN
    INSERT OR REPLACE INTO user_progress (
        user_id,
        pose_name,
        total_assessments,
        average_score,
        best_score,
        worst_score,
        latest_score,
        first_assessment_time,
        last_assessment_time,
        updated_at
    )
    SELECT
        NEW.user_id,
        NEW.pose_name,
        COALESCE((
            SELECT total_assessments
            FROM user_progress
            WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
        ), 0) + 1,
        COALESCE((
            SELECT average_score
            FROM user_progress
            WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
        ), 0) * (
            SELECT COALESCE(total_assessments, 0)
            FROM user_progress
            WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
        ) / (
            COALESCE((
                SELECT total_assessments
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ), 0) + 1
        ) + NEW.total_score / (
            COALESCE((
                SELECT total_assessments
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ), 0) + 1
        ),
        CASE
            WHEN (
                SELECT best_score
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ) IS NULL THEN NEW.total_score
            WHEN NEW.total_score > (
                SELECT best_score
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ) THEN NEW.total_score
            ELSE (
                SELECT best_score
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            )
        END,
        CASE
            WHEN (
                SELECT worst_score
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ) IS NULL THEN NEW.total_score
            WHEN NEW.total_score < (
                SELECT worst_score
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ) THEN NEW.total_score
            ELSE (
                SELECT worst_score
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            )
        END,
        NEW.total_score,
        CASE
            WHEN (
                SELECT first_assessment_time
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            ) IS NULL THEN NEW.assessment_time
            ELSE (
                SELECT first_assessment_time
                FROM user_progress
                WHERE user_id = NEW.user_id AND pose_name = NEW.pose_name
            )
        END,
        NEW.assessment_time,
        datetime('now', 'localtime')
    ;
END;

-- 更新动作标准时间戳触发器
DROP TRIGGER IF EXISTS trigger_update_pose_timestamp;
CREATE TRIGGER trigger_update_pose_timestamp
AFTER UPDATE ON pose_standard
BEGIN
    UPDATE pose_standard
    SET updated_at = datetime('now', 'localtime')
    WHERE id = NEW.id;
END;

-- ================================================================
-- 创建存储过程 (模拟)
-- ================================================================

-- 获取用户评估历史
-- SQLite不支持存储过程,此处作为文档说明
/*
CREATE PROCEDURE get_user_assessment_history(
    IN p_user_id INTEGER,
    IN p_limit INTEGER
)
BEGIN
    SELECT
        ar.*,
        ps.difficulty_level
    FROM assessment_record ar
    LEFT JOIN pose_standard ps ON ar.pose_name = ps.pose_name
    WHERE ar.user_id = p_user_id
    ORDER BY ar.assessment_time DESC
    LIMIT p_limit;
END;
*/

-- ================================================================
-- 数据库维护脚本
-- ================================================================

-- 定期清理旧日志（保留90天）
-- DELETE FROM system_log WHERE created_at < datetime('now', '-90 days');

-- 定期清理临时视频数据（保留7天）
-- DELETE FROM video_data WHERE processing_status = 'pending' AND upload_time < datetime('now', '-7 days');

-- 优化数据库
-- PRAGMA optimize;

-- ================================================================
-- 数据库设计说明
-- ================================================================
/*
1. 表设计原则:
   - 遵循第三范式,减少数据冗余
   - 合理使用外键约束保证数据完整性
   - 创建适当的索引提升查询性能

2. 主要表说明:
   - user: 用户信息表
   - assessment_record: 评估记录表,存储所有评估结果
   - pose_standard: 动作标准库表
   - video_data: 视频数据表
   - user_progress: 用户进步跟踪表
   - system_log: 系统日志表
   - feedback: 用户反馈表
   - tag: 标签表
   - assessment_tag: 评估记录与标签关联表
   - statistics: 统计数据表

3. 数据类型选择:
   - INTEGER: 主键、外键、计数器
   - VARCHAR: 短文本、名称
   - TEXT: 长文本、JSON数据
   - FLOAT: 分数、角度、时间
   - DATETIME: 时间戳
   - BOOLEAN: 布尔值

4. 索引设计:
   - 所有外键字段创建索引
   - 常用查询字段创建索引
   - 复合索引优化多条件查询

5. 触发器设计:
   - trigger_update_user_progress: 自动更新用户进步记录
   - trigger_update_pose_timestamp: 自动更新修改时间

6. 视图设计:
   - view_user_assessment_stats: 用户评估统计
   - view_pose_assessment_stats: 动作评估统计
   - view_daily_stats: 每日统计

7. JSON字段说明:
   - angle_data: 角度数据(JSON格式)
   - graph_data: 姿态图数据(JSON格式)
   - problems: 问题列表(JSON数组)
   - suggestions: 建议列表(JSON数组)
   - common_errors: 常见错误(JSON数组)
   - suggestion_templates: 建议模板(JSON数组)
   - improvement_trend: 改进趋势(JSON数组)
   - achievements: 成就列表(JSON数组)

8. 扩展性考虑:
   - 支持新增动作类型
   - 支持新增评估维度
   - 支持多标签系统
   - 预留统计数据表
   - 预留反馈机制
*/
