"""
数据库管理模块
提供数据库初始化、CRUD操作、统计查询等功能
"""

import os
import sqlite3
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path or os.environ.get(
            "YOGA_DB_PATH",
            str(Path(tempfile.gettempdir()) / "yuga_test" / "yoga_assessment.db")
        )
        self._ensure_db_dir()
        self.init_database()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """获取数据库连接(上下文管理器)"""
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """初始化数据库,创建表结构"""
        # 读取SQL文件
        schema_path = Path(__file__).parent.parent / "database_schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"数据库Schema文件不存在: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 执行SQL脚本
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            print("数据库初始化成功")

    # ==================== 用户相关操作 ====================

    def create_user(self, username: str, password: str, email: str = None, role: str = 'user') -> int:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码(应已加密)
            email: 邮箱
            role: 角色(user/admin)

        Returns:
            用户ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user (username, password, email, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password, email, role, datetime.now()))
            return cursor.lastrowid

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_last_login(self, user_id: int):
        """更新用户最后登录时间"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user SET last_login = ? WHERE id = ?
            """, (datetime.now(), user_id))

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取用户列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM user
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    def update_user_role(self, user_id: int, role: str) -> bool:
        """更新用户角色"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET role = ? WHERE id = ?", (role, user_id))
            return cursor.rowcount > 0

    def update_user_password(self, user_id: int, password_hash: str) -> bool:
        """更新用户密码哈希。"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET password = ? WHERE id = ?", (password_hash, user_id))
            return cursor.rowcount > 0

    def set_user_active(self, user_id: int, is_active: bool) -> bool:
        """启用/禁用用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
            return cursor.rowcount > 0

    # ==================== 评估记录相关操作 ====================

    def create_assessment_record(self, record_data: Dict) -> int:
        """
        创建评估记录

        Args:
            record_data: 评估记录字典,包含:
                - user_id: 用户ID
                - video_name: 视频名称
                - video_path: 视频路径
                - pose_name: 动作名称
                - total_score: 总分
                - structure_score: 结构分
                - alignment_score: 正位分
                - stability_score: 稳定分
                - angle_data: 角度数据(JSON)
                - graph_data: 姿态图数据(JSON)
                - stability_rating: 稳定性评分
                - problems: 问题列表(JSON)
                - suggestions: 建议列表(JSON)
                - annotated_video_path: 标注视频路径
                - video_duration: 视频时长
                - video_fps: 帧率
                - video_resolution: 分辨率
                - frame_count: 帧数
                - processing_time: 处理时间
                - model_used: 使用的模型

        Returns:
            评估记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assessment_record (
                    user_id, video_name, video_path, pose_name, assessment_time,
                    total_score, structure_score, alignment_score, stability_score,
                    angle_data, graph_data, stability_rating, problems, suggestions,
                    annotated_video_path, video_duration, video_fps, video_resolution,
                    frame_count, processing_time, model_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data.get('user_id'),
                record_data.get('video_name'),
                record_data.get('video_path'),
                record_data.get('pose_name'),
                datetime.now(),
                record_data.get('total_score'),
                record_data.get('structure_score'),
                record_data.get('alignment_score'),
                record_data.get('stability_score'),
                json.dumps(record_data.get('angle_data', {}), ensure_ascii=False),
                json.dumps(record_data.get('graph_data', {}), ensure_ascii=False),
                record_data.get('stability_rating'),
                json.dumps(record_data.get('problems', []), ensure_ascii=False),
                json.dumps(record_data.get('suggestions', []), ensure_ascii=False),
                record_data.get('annotated_video_path'),
                record_data.get('video_duration'),
                record_data.get('video_fps'),
                record_data.get('video_resolution'),
                record_data.get('frame_count'),
                record_data.get('processing_time'),
                record_data.get('model_used')
            ))
            return cursor.lastrowid

    def get_assessment_record(self, record_id: int) -> Optional[Dict]:
        """获取评估记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assessment_record WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                return None

            record = dict(row)
            # 解析JSON字段
            for field in ['angle_data', 'graph_data', 'problems', 'suggestions']:
                if record.get(field):
                    record[field] = json.loads(record[field])
            return record

    def get_user_assessments(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取用户的评估记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM assessment_record
                WHERE user_id = ?
                ORDER BY assessment_time DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            records = [dict(row) for row in cursor.fetchall()]

            # 解析JSON字段
            for record in records:
                for field in ['angle_data', 'graph_data', 'problems', 'suggestions']:
                    if record.get(field):
                        record[field] = json.loads(record[field])

            return records

    def get_assessments_by_pose(self, pose_name: str, limit: int = 50) -> List[Dict]:
        """获取指定动作的所有评估记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM assessment_record
                WHERE pose_name = ?
                ORDER BY assessment_time DESC
                LIMIT ?
            """, (pose_name, limit))
            records = [dict(row) for row in cursor.fetchall()]

            # 解析JSON字段
            for record in records:
                for field in ['angle_data', 'graph_data', 'problems', 'suggestions']:
                    if record.get(field):
                        record[field] = json.loads(record[field])

            return records

    def search_assessments(self, user_id: Optional[int] = None,
                         pose_name: Optional[str] = None,
                         min_score: Optional[float] = None,
                         max_score: Optional[float] = None,
                         limit: int = 50) -> List[Dict]:
        """搜索评估记录"""
        query = "SELECT * FROM assessment_record WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if pose_name:
            query += " AND pose_name = ?"
            params.append(pose_name)

        if min_score:
            query += " AND total_score >= ?"
            params.append(min_score)

        if max_score:
            query += " AND total_score <= ?"
            params.append(max_score)

        query += " ORDER BY assessment_time DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            records = [dict(row) for row in cursor.fetchall()]

            # 解析JSON字段
            for record in records:
                for field in ['angle_data', 'graph_data', 'problems', 'suggestions']:
                    if record.get(field):
                        record[field] = json.loads(record[field])

            return records

    # ==================== 动作标准相关操作 ====================

    def create_pose_standard(self, standard_data: Dict) -> int:
        """
        创建动作标准

        Args:
            standard_data: 动作标准字典

        Returns:
            动作标准ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pose_standard (
                    pose_name, pose_name_en, category, difficulty_level,
                    hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max,
                    spine_min, spine_max, description, benefits, contraindications,
                    common_errors, suggestion_templates, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                standard_data.get('pose_name'),
                standard_data.get('pose_name_en'),
                standard_data.get('category'),
                standard_data.get('difficulty_level'),
                standard_data.get('hip_min'),
                standard_data.get('hip_max'),
                standard_data.get('knee_min'),
                standard_data.get('knee_max'),
                standard_data.get('shoulder_min'),
                standard_data.get('shoulder_max'),
                standard_data.get('spine_min'),
                standard_data.get('spine_max'),
                standard_data.get('description'),
                standard_data.get('benefits'),
                standard_data.get('contraindications'),
                json.dumps(standard_data.get('common_errors', []), ensure_ascii=False),
                json.dumps(standard_data.get('suggestion_templates', []), ensure_ascii=False),
                standard_data.get('is_active', True)
            ))
            return cursor.lastrowid

    def get_pose_standard(self, pose_name: str) -> Optional[Dict]:
        """获取动作标准"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM pose_standard WHERE pose_name = ? AND is_active = 1
            """, (pose_name,))
            row = cursor.fetchone()
            if not row:
                return None

            standard = dict(row)
            # 解析JSON字段
            if standard.get('common_errors'):
                standard['common_errors'] = json.loads(standard['common_errors'])
            if standard.get('suggestion_templates'):
                standard['suggestion_templates'] = json.loads(standard['suggestion_templates'])
            return standard

    def list_pose_standards(self, category: Optional[str] = None,
                          difficulty: Optional[str] = None) -> List[Dict]:
        """获取动作标准列表"""
        query = "SELECT * FROM pose_standard WHERE is_active = 1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if difficulty:
            query += " AND difficulty_level = ?"
            params.append(difficulty)

        query += " ORDER BY pose_name"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            standards = [dict(row) for row in cursor.fetchall()]

            # 解析JSON字段
            for standard in standards:
                if standard.get('common_errors'):
                    standard['common_errors'] = json.loads(standard['common_errors'])
                if standard.get('suggestion_templates'):
                    standard['suggestion_templates'] = json.loads(standard['suggestion_templates'])

            return standards

    def update_pose_standard(self, pose_name: str, update_data: Dict) -> bool:
        """更新动作标准"""
        set_clauses = []
        params = []

        for key, value in update_data.items():
            if key in ['pose_name', 'pose_name_en', 'category', 'difficulty_level',
                      'description', 'benefits', 'contraindications', 'is_active']:
                set_clauses.append(f"{key} = ?")
                params.append(value)
            elif key in ['common_errors', 'suggestion_templates']:
                set_clauses.append(f"{key} = ?")
                params.append(json.dumps(value, ensure_ascii=False))
            elif key in ['hip_min', 'hip_max', 'knee_min', 'knee_max',
                       'shoulder_min', 'shoulder_max', 'spine_min', 'spine_max']:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        if not set_clauses:
            return False

        params.append(pose_name)
        query = f"UPDATE pose_standard SET {', '.join(set_clauses)} WHERE pose_name = ?"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def delete_pose_standard(self, pose_name: str) -> bool:
        """删除动作标准(软删除)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pose_standard SET is_active = 0 WHERE pose_name = ?
            """, (pose_name,))
            return cursor.rowcount > 0

    # ==================== 视频数据相关操作 ====================

    def create_video_record(self, video_data: Dict) -> int:
        """创建视频记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO video_data (
                    user_id, video_name, original_filename, file_path, file_size,
                    file_format, video_duration, video_fps, video_width,
                    video_height, upload_time, upload_ip, processing_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_data.get('user_id'),
                video_data.get('video_name'),
                video_data.get('original_filename'),
                video_data.get('file_path'),
                video_data.get('file_size'),
                video_data.get('file_format'),
                video_data.get('video_duration'),
                video_data.get('video_fps'),
                video_data.get('video_width'),
                video_data.get('video_height'),
                datetime.now(),
                video_data.get('upload_ip'),
                video_data.get('processing_status', 'pending')
            ))
            return cursor.lastrowid

    def update_video_status(self, video_id: int, status: str,
                          error: Optional[str] = None,
                          assessment_record_id: Optional[int] = None):
        """更新视频处理状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_data
                SET processing_status = ?,
                    processing_end_time = ?,
                    processing_error = ?,
                    assessment_record_id = ?
                WHERE id = ?
            """, (
                status,
                datetime.now(),
                error,
                assessment_record_id,
                video_id
            ))

    # ==================== 用户进步相关操作 ====================

    def get_user_progress(self, user_id: int, pose_name: str = None) -> Optional[Dict]:
        """获取用户进步记录"""
        if pose_name:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_progress
                    WHERE user_id = ? AND pose_name = ?
                """, (user_id, pose_name))
                row = cursor.fetchone()
                if not row:
                    return None

                progress = dict(row)
                # 解析JSON字段
                if progress.get('improvement_trend'):
                    progress['improvement_trend'] = json.loads(progress['improvement_trend'])
                if progress.get('achievements'):
                    progress['achievements'] = json.loads(progress['achievements'])
                return progress
        else:
            # 获取用户所有动作的进步记录
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_progress WHERE user_id = ?
                """, (user_id,))
                rows = cursor.fetchall()

                progress_list = []
                for row in rows:
                    progress = dict(row)
                    if progress.get('improvement_trend'):
                        progress['improvement_trend'] = json.loads(progress['improvement_trend'])
                    if progress.get('achievements'):
                        progress['achievements'] = json.loads(progress['achievements'])
                    progress_list.append(progress)

                return progress_list

    # ==================== 统计相关操作 ====================

    def get_user_stats(self, user_id: int) -> Dict:
        """获取用户统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM view_user_assessment_stats WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_pose_stats(self, pose_name: str = None) -> List[Dict]:
        """获取动作统计信息"""
        if pose_name:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM view_pose_assessment_stats WHERE pose_name = ?
                """, (pose_name,))
                row = cursor.fetchone()
                return [dict(row)] if row else []
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM view_pose_assessment_stats
                    ORDER BY total_assessments DESC
                """)
                return [dict(row) for row in cursor.fetchall()]

    def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """获取每日统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM view_daily_stats
                ORDER BY stat_date DESC
                LIMIT ?
            """, (days,))
            return [dict(row) for row in cursor.fetchall()]

    def get_system_overview(self) -> Dict:
        """获取系统总览"""
        stats = {}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 总用户数
            cursor.execute("SELECT COUNT(*) as count FROM user")
            stats['total_users'] = cursor.fetchone()['count']

            # 总评估数
            cursor.execute("SELECT COUNT(*) as count FROM assessment_record")
            stats['total_assessments'] = cursor.fetchone()['count']

            # 今日评估数
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM assessment_record
                WHERE DATE(assessment_time) = DATE('now', 'localtime')
            """)
            stats['today_assessments'] = cursor.fetchone()['count']

            # 平均分数
            cursor.execute("SELECT AVG(total_score) as avg_score FROM assessment_record")
            avg = cursor.fetchone()['avg_score']
            stats['average_score'] = round(avg, 2) if avg else 0

            # 动作种类数
            cursor.execute("SELECT COUNT(DISTINCT pose_name) as count FROM pose_standard WHERE is_active = 1")
            stats['pose_types'] = cursor.fetchone()['count']

            # 活跃用户数(7天内)
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM assessment_record
                WHERE assessment_time > datetime('now', '-7 days')
            """)
            stats['active_users'] = cursor.fetchone()['count']

        return stats

    # ==================== 日志相关操作 ====================

    def add_log(self, log_type: str, log_level: str, action: str,
                message: str, user_id: Optional[int] = None,
                details: Optional[str] = None, ip_address: Optional[str] = None):
        """添加系统日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_log (
                    user_id, log_type, log_level, action, message,
                    details, ip_address, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, log_type, log_level, action, message,
                details, ip_address, datetime.now()
            ))

    def get_logs(self, log_type: Optional[str] = None,
                log_level: Optional[str] = None,
                user_id: Optional[int] = None,
                limit: int = 100) -> List[Dict]:
        """获取系统日志"""
        query = "SELECT * FROM system_log WHERE 1=1"
        params = []

        if log_type:
            query += " AND log_type = ?"
            params.append(log_type)

        if log_level:
            query += " AND log_level = ?"
            params.append(log_level)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== 反馈相关操作 ====================

    def create_feedback(self, feedback_data: Dict) -> int:
        """创建用户反馈"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (
                    user_id, assessment_record_id, feedback_type,
                    rating, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                feedback_data.get('user_id'),
                feedback_data.get('assessment_record_id'),
                feedback_data.get('feedback_type'),
                feedback_data.get('rating'),
                feedback_data.get('comment'),
                datetime.now()
            ))
            return cursor.lastrowid

    def get_feedbacks(self, feedback_type: Optional[str] = None,
                     is_resolved: Optional[bool] = None,
                     limit: int = 50) -> List[Dict]:
        """获取反馈列表"""
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []

        if feedback_type:
            query += " AND feedback_type = ?"
            params.append(feedback_type)

        if is_resolved is not None:
            query += " AND is_resolved = ?"
            params.append(is_resolved)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== 标签相关操作 ====================

    def create_tag(self, tag_name: str, tag_type: str, description: str = None) -> int:
        """创建标签"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tag (tag_name, tag_type, description, created_at)
                VALUES (?, ?, ?, ?)
            """, (tag_name, tag_type, description, datetime.now()))
            return cursor.lastrowid

    def get_tags(self, tag_type: Optional[str] = None) -> List[Dict]:
        """获取标签列表"""
        if tag_type:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tag WHERE tag_type = ? ORDER BY tag_name
                """, (tag_type,))
                return [dict(row) for row in cursor.fetchall()]
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tag ORDER BY tag_name")
                return [dict(row) for row in cursor.fetchall()]

    def add_tag_to_assessment(self, assessment_id: int, tag_id: int):
        """为评估记录添加标签"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO assessment_tag (assessment_id, tag_id, created_at)
                VALUES (?, ?, ?)
            """, (assessment_id, tag_id, datetime.now()))

    def get_assessment_tags(self, assessment_id: int) -> List[Dict]:
        """获取评估记录的标签"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.* FROM tag t
                INNER JOIN assessment_tag at ON t.id = at.tag_id
                WHERE at.assessment_id = ?
            """, (assessment_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== 维护相关操作 ====================

    def cleanup_old_logs(self, days: int = 90):
        """清理旧日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM system_log
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            return cursor.rowcount

    def cleanup_pending_videos(self, days: int = 7):
        """清理长时间未处理的视频"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM video_data
                WHERE processing_status = 'pending'
                AND upload_time < datetime('now', '-{} days')
            """.format(days))
            return cursor.rowcount

    def optimize_database(self):
        """优化数据库"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA optimize")
            print("数据库优化完成")


# ==================== 数据库使用示例 ====================

if __name__ == "__main__":
    # 初始化数据库
    db = DatabaseManager()

    # 示例1: 创建用户
    user_id = db.create_user(
        username="test_user",
        password="hashed_password",
        email="test@example.com",
        role="user"
    )
    print(f"创建用户成功, ID: {user_id}")

    # 示例2: 获取动作标准
    pose_standard = db.get_pose_standard("下犬式")
    if pose_standard:
        print(f"动作标准: {pose_standard['pose_name']}")
        print(f"髋关节范围: {pose_standard['hip_min']}° - {pose_standard['hip_max']}°")

    # 示例3: 创建评估记录
    assessment_data = {
        'user_id': user_id,
        'video_name': 'test_video.mp4',
        'video_path': '/path/to/video.mp4',
        'pose_name': '下犬式',
        'total_score': 85.5,
        'structure_score': 52.0,
        'alignment_score': 25.5,
        'stability_score': 8.0,
        'angle_data': {'left_knee': 170.5, 'right_knee': 168.2},
        'graph_data': {'nodes': 33, 'edges': 48},
        'stability_rating': 8.5,
        'problems': ['膝关节过度弯曲', '肩膀耸起'],
        'suggestions': ['放松肩膀', '伸直膝关节'],
        'annotated_video_path': '/path/to/annotated.mp4',
        'video_duration': 30.0,
        'video_fps': 30.0,
        'video_resolution': '1920x1080',
        'frame_count': 900,
        'processing_time': 18.5,
        'model_used': 'qwen3.5:4b'
    }
    record_id = db.create_assessment_record(assessment_data)
    print(f"创建评估记录成功, ID: {record_id}")

    # 示例4: 获取用户评估记录
    assessments = db.get_user_assessments(user_id)
    print(f"用户评估记录数: {len(assessments)}")

    # 示例5: 获取系统统计
    stats = db.get_system_overview()
    print(f"系统统计: {stats}")

    # 示例6: 获取动作统计
    pose_stats = db.get_pose_stats()
    print(f"动作统计数: {len(pose_stats)}")
    for stat in pose_stats[:3]:
        print(f"  {stat['pose_name']}: {stat['total_assessments']}次评估, 平均分{stat['avg_score']:.1f}")

    # 示例7: 添加标签
    tag_id = db.create_tag("稳定", "quality", "动作稳定,晃动小")
    db.add_tag_to_assessment(record_id, tag_id)
    print(f"添加标签成功, 标签ID: {tag_id}")

    # 示例8: 获取用户进步
    progress = db.get_user_progress(user_id, "下犬式")
    if progress:
        print(f"用户进步记录: 评估{progress['total_assessments']}次, 平均分{progress['average_score']:.1f}")
