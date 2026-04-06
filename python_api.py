"""
Python Flask REST API 后端
与 JavaScript 前端配合使用
端口: 5000
"""

import os
import sys
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
from pathlib import Path
from datetime import datetime
import json
import time
import threading
from functools import wraps

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.video_reader import VideoReader
from src.pose_detector import PoseDetector
from src.angle_calculator import AngleCalculator
from src.stats_calculator import StatsCalculator
from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.multimodal_client import MultimodalClient
from src.result_parser import ResultParser
from src.simple_evaluator import SimpleEvaluator
from src.database import DatabaseManager
from src.auth import (
    hash_password,
    verify_password,
    create_session,
    create_access_token,
    create_refresh_token,
    get_user_id_from_access_token,
    get_user_id_from_refresh_token,
    invalidate_access_token,
    invalidate_refresh_token,
    invalidate_user_sessions,
    refresh_session
)
from config.settings import POSE_STANDARDS, MULTIMODAL_CONFIG

app = Flask(__name__)
CORS(app)
TEST_MODE = os.environ.get("YOGA_TEST_MODE", "").strip().lower() in {"1", "true", "yes", "on"}

# 初始化各模块
print("Initializing modules...")
if TEST_MODE:
    video_reader = None
    pose_detector = None
    angle_calculator = None
    stats_calculator = None
    prompt_builder = None
    ollama_client = None
    multimodal_client = None
    result_parser = None
    simple_evaluator = None
else:
    video_reader = VideoReader()
    pose_detector = PoseDetector()
    angle_calculator = AngleCalculator()
    stats_calculator = StatsCalculator()
    prompt_builder = PromptBuilder()
    ollama_client = OllamaClient()
    multimodal_client = MultimodalClient()  # 多模态 API 客户端
    result_parser = ResultParser()
    simple_evaluator = SimpleEvaluator()
db = DatabaseManager()

# 检查 Ollama 连接
ollama_available = False if TEST_MODE else ollama_client.check_connection()
print(f"Ollama connection: {'skipped in test mode' if TEST_MODE else ('available' if ollama_available else 'unavailable')}")

# 检查多模态 API 连接
multimodal_available = False if TEST_MODE else multimodal_client.check_connection()
print(f"Multimodal API connection: {'skipped in test mode' if TEST_MODE else ('available' if multimodal_available else 'unavailable')}")

# 创建临时目录
UPLOAD_DIR = Path(project_root) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 内存中的评估记录
assessments = {}
next_assessment_id = 1
assessment_lock = threading.Lock()


def to_api_role(db_role: str) -> str:
    """Map stored database roles to frontend-facing roles."""
    return 'learner' if db_role == 'user' else db_role


def ensure_default_admin():
    default_admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    admin_user = db.get_user_by_username('admin')

    if not admin_user:
        db.create_user('admin', hash_password(default_admin_password), 'admin@example.com', role='admin')
        print(f"Created default admin account: admin / {default_admin_password}")
        return

    stored_password = admin_user.get('password', '')
    if not isinstance(stored_password, str) or not stored_password.startswith(('pbkdf2:', 'scrypt:')):
        db.update_user_password(admin_user['id'], hash_password(default_admin_password))
        print("Updated default admin password to a hashed value.")


ensure_default_admin()


def process_assessment_task(assessment_id: int, user: dict, video_path: Path, video_filename: str, pose_name: str, remote_addr: str):
    """后台处理单个评估任务，避免上传请求长时间阻塞。"""
    try:
        if TEST_MODE:
            assessments[assessment_id]['status'] = 'completed'
            assessments[assessment_id]['result'] = {
                'total_score': 88.0,
                'structure_score': 52.0,
                'alignment_score': 28.0,
                'stability_score': 8.0,
                'angle_data': {
                    'left_elbow': 170,
                    'right_elbow': 168,
                    'left_knee': 175,
                    'right_knee': 174,
                    'left_hip': 160,
                    'right_hip': 161
                },
                'problems': ['Test mode placeholder issue'],
                'suggestions': ['Test mode placeholder suggestion']
            }
            return

        print(f"开始处理视频 {video_path} (姿势: {pose_name}, assessment_id={assessment_id})")
        start_time = time.time()

        # 1. 读取视频
        video_info, frames = video_reader.read(str(video_path))
        print(f"读取成功: {len(frames)} 帧")

        # 2. 关键点检测
        print("检测关键点...")
        landmarks_seq = pose_detector.detect_sequence(frames)

        valid_landmarks = [lm for lm in landmarks_seq if lm is not None]
        if not valid_landmarks:
            assessments[assessment_id]['status'] = 'failed'
            assessments[assessment_id]['result'] = {'error': '未检测到人体关键点'}
            print("评估失败: 无法检测关键点")
            return

        # 3. 角度计算
        print("计算角度...")
        angles_seq = angle_calculator.compute_all(landmarks_seq)

        # 4. 统计分析
        print("分析统计...")
        stats = stats_calculator.compute(angles_seq)
        stability_score = stats_calculator.compute_stability(landmarks_seq)

        # 5. 构建提示词
        pose_standard = POSE_STANDARDS.get(pose_name) or {}
        prompt = prompt_builder.build(stats, stability_score, pose_name, pose_standard)

        # 6. 调用模型或降级到简单评估
        assessment_result = None
        if multimodal_available:
            try:
                print("调用多模态 API...")
                middle_idx = len(frames) // 2
                key_frame = frames[middle_idx]
                model_response = multimodal_client.analyze_image_with_prompt(key_frame, prompt)
                print(f"多模态 API 返回内容长度: {len(model_response)}")
                assessment_result = result_parser.parse(model_response)
                if not assessment_result.get('success', False):
                    print("多模态结果解析失败，降级到简单评估")
                    assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
            except Exception as e:
                print(f"多模态 API 调用异常: {e}，降级到简单评估")
                assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
        elif ollama_available:
            try:
                print("调用 Ollama 模型...")
                middle_idx = len(frames) // 2
                key_frame = frames[middle_idx]
                model_response = ollama_client.generate(prompt, key_frame)
                assessment_result = result_parser.parse(model_response)
                if not assessment_result.get('success', False):
                    print("Ollama 结果解析失败，降级到简单评估")
                    assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
            except Exception as e:
                print(f"Ollama 调用异常: {e}，降级到简单评估")
                assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
        else:
            print("未检测到可用模型，使用简单评估")
            assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)

        # 7. 提取分数
        if assessment_result is None:
            print("警告: 评估结果为空，使用默认分数")
            result = {
                'total_score': 75.0,
                'structure_score': 45.0,
                'alignment_score': 22.5,
                'stability_score': 7.5,
                'angle_data': stats,
                'problems': ['无法获取详细评估'],
                'suggestions': ['请尝试重新上传视频']
            }
        else:
            score_data = assessment_result.get('data', {}).get('score', {}) if assessment_result.get('data') else {}
            total_score = score_data.get('total', 80) if score_data.get('total') is not None else 80
            structure_score = score_data.get('accuracy', 50) if score_data.get('accuracy') is not None else 50
            alignment_score = score_data.get('stability', 25) if score_data.get('stability') is not None else 25
            stability_score_val = score_data.get('coordination', 5) if score_data.get('coordination') is not None else 5

            problems = assessment_result.get('data', {}).get('problems', []) if assessment_result.get('data') else []
            if not isinstance(problems, list):
                problems = []

            suggestions = assessment_result.get('data', {}).get('suggestions', []) if assessment_result.get('data') else []
            if not isinstance(suggestions, list):
                suggestions = []

            result = {
                'total_score': float(total_score),
                'structure_score': float(structure_score),
                'alignment_score': float(alignment_score),
                'stability_score': float(stability_score_val),
                'angle_data': stats,
                'problems': problems,
                'suggestions': suggestions
            }

        record_data = {
            'user_id': user['id'],
            'video_name': video_filename,
            'video_path': str(video_path),
            'pose_name': pose_name,
            'total_score': result['total_score'],
            'structure_score': result['structure_score'],
            'alignment_score': result['alignment_score'],
            'stability_score': result['stability_score'],
            'angle_data': stats,
            'graph_data': {},
            'stability_rating': stability_score,
            'problems': result['problems'],
            'suggestions': result['suggestions'],
            'annotated_video_path': None,
            'video_duration': video_info.get('duration') if isinstance(video_info, dict) else None,
            'video_fps': video_info.get('fps') if isinstance(video_info, dict) else None,
            'video_resolution': f"{video_info.get('width', 0)}x{video_info.get('height', 0)}" if isinstance(video_info, dict) else None,
            'frame_count': len(frames),
            'processing_time': round(time.time() - start_time, 2),
            'model_used': 'qwen' if multimodal_available else 'simple_evaluator'
        }
        assessments[assessment_id]['db_record_id'] = db.create_assessment_record(record_data)
        assessments[assessment_id]['status'] = 'completed'
        assessments[assessment_id]['result'] = result
        print(f"评估完成: ID={assessment_id}, 分数={result['total_score']}")

    except Exception as e:
        import traceback
        print(f"处理异常: {e}")
        print(traceback.format_exc())
        assessments[assessment_id]['status'] = 'failed'
        assessments[assessment_id]['result'] = {'error': str(e)}
        db.add_log('error', 'ERROR', 'assessment_failure', str(e), user_id=user['id'], ip_address=remote_addr)


def get_auth_token() -> str:
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1].strip()
    return ''


def get_authenticated_user():
    token = get_auth_token()
    user_id = get_user_id_from_access_token(token)
    if not user_id:
        return None
    return db.get_user_by_id(user_id)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_authenticated_user()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        return func(user=user, *args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(user, *args, **kwargs):
        if user.get('role') != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        return func(user=user, *args, **kwargs)
    return wrapper


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if db.get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 409

    password_hash = hash_password(password)
    user_id = db.create_user(username, password_hash, email, role='user')
    session_data = create_session(user_id)

    return jsonify({
        'user': {
            'id': user_id,
            'username': username,
            'email': email,
            'role': 'learner'
        },
        'access_token': session_data['access_token'],
        'refresh_token': session_data['refresh_token'],
        'expires_in': session_data['expires_in'],
        'refresh_expires_in': session_data['refresh_expires_in']
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    user = db.get_user_by_username(username)
    if not user or not verify_password(password, user['password']):
        return jsonify({'error': '用户名或密码错误'}), 401

    if not user.get('is_active', 1):
        return jsonify({'error': '用户已禁用'}), 403

    db.update_user_last_login(user['id'])
    session_data = create_session(user['id'])

    return jsonify({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user.get('email'),
            'role': to_api_role(user.get('role', 'user'))
        },
        'access_token': session_data['access_token'],
        'refresh_token': session_data['refresh_token'],
        'expires_in': session_data['expires_in'],
        'refresh_expires_in': session_data['refresh_expires_in']
    })


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json(force=True)
    refresh_token = data.get('refresh_token', '').strip()
    if not refresh_token:
        return jsonify({'error': 'refresh_token 不能为空'}), 400

    session_data = refresh_session(refresh_token)
    if not session_data:
        return jsonify({'error': 'refresh_token 无效或已过期'}), 401

    return jsonify({
        'access_token': session_data['access_token'],
        'refresh_token': session_data['refresh_token'],
        'expires_in': session_data['expires_in'],
        'refresh_expires_in': session_data['refresh_expires_in']
    })


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout(user):
    token = get_auth_token()
    refresh_token = None
    try:
        body = request.get_json(silent=True) or {}
        refresh_token = body.get('refresh_token')
    except Exception:
        refresh_token = None

    if token:
        invalidate_access_token(token)
    if refresh_token:
        invalidate_refresh_token(refresh_token)
    else:
        invalidate_user_sessions(user['id'])

    return jsonify({'message': '退出成功'})


@app.route('/api/auth/me', methods=['GET'])
@login_required
def profile(user):
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user.get('email'),
        'role': to_api_role(user.get('role', 'user')),
        'is_active': bool(user.get('is_active', 1)),
        'last_login': user.get('last_login')
    })


@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def list_users(user):
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    return jsonify(db.list_users(limit=limit, offset=offset))


@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user(user):
    data = request.get_json(force=True)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'learner')

    valid_roles = ['learner', 'coach', 'admin']
    if role not in valid_roles:
        return jsonify({'error': '无效角色'}), 400

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if db.get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 409

    password_hash = hash_password(password)
    user_id = db.create_user(username, password_hash, email, role=role)
    return jsonify({'id': user_id, 'username': username, 'email': email, 'role': role})


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user, user_id):
    data = request.get_json(force=True)
    role = data.get('role')
    is_active = data.get('is_active')
    updated = False

    if role:
        valid_roles = ['learner', 'coach', 'admin']
        if role not in valid_roles:
            return jsonify({'error': '无效角色'}), 400
        updated = db.update_user_role(user_id, role)

    if is_active is not None:
        updated = db.set_user_active(user_id, bool(is_active)) or updated

    if not updated:
        return jsonify({'error': '用户更新失败'}), 400

    return jsonify({'id': user_id, 'role': role, 'is_active': bool(is_active)})


@app.route('/api/user/assessments', methods=['GET'])
@login_required
def list_user_assessments(user):
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    records = db.get_user_assessments(user['id'], limit=limit, offset=offset)
    return jsonify(records)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'yoga-assessment-api',
        'status': 'ok',
        'version': '0.1.0',
        'backend': 'Python Flask'
    })


@app.route('/api/stats', methods=['GET'])
def public_stats():
    """公开统计信息"""
    stats = db.get_system_overview()
    return jsonify({
        'total_assessments': stats.get('total_assessments', 0),
        'total_users': stats.get('total_users', 0),
        'avg_score': stats.get('average_score', 0),
        'pose_types': stats.get('pose_types', 0)
    })


@app.route('/api/pose/standards', methods=['GET'])
def get_pose_standards():
    """获取瑜伽姿态标准"""
    poses = [
        {
            'id': 1,
            'pose_name': 'Mountain Pose',
            'difficulty_level': 'Beginner',
            'hip_min': 170.0,
            'hip_max': 180.0,
            'knee_min': 165.0,
            'knee_max': 180.0,
            'shoulder_min': 170.0,
            'shoulder_max': 180.0,
            'spine_min': 0.0,
            'spine_max': 10.0
        },
        {
            'id': 2,
            'pose_name': 'Tree Pose',
            'difficulty_level': 'Intermediate',
            'hip_min': 150.0,
            'hip_max': 175.0,
            'knee_min': 160.0,
            'knee_max': 180.0,
            'shoulder_min': 160.0,
            'shoulder_max': 180.0,
            'spine_min': 0.0,
            'spine_max': 15.0
        },
        {
            'id': 3,
            'pose_name': 'Warrior II',
            'difficulty_level': 'Intermediate',
            'hip_min': 140.0,
            'hip_max': 170.0,
            'knee_min': 155.0,
            'knee_max': 175.0,
            'shoulder_min': 160.0,
            'shoulder_max': 180.0,
            'spine_min': 0.0,
            'spine_max': 20.0
        },
        {
            'id': 4,
            'pose_name': 'Triangle Pose',
            'difficulty_level': 'Intermediate',
            'hip_min': 150.0,
            'hip_max': 175.0,
            'knee_min': 160.0,
            'knee_max': 180.0,
            'shoulder_min': 155.0,
            'shoulder_max': 180.0,
            'spine_min': 5.0,
            'spine_max': 25.0
        },
        {
            'id': 5,
            'pose_name': 'Chair Pose',
            'difficulty_level': 'Beginner',
            'hip_min': 130.0,
            'hip_max': 160.0,
            'knee_min': 150.0,
            'knee_max': 175.0,
            'shoulder_min': 165.0,
            'shoulder_max': 180.0,
            'spine_min': 0.0,
            'spine_max': 15.0
        }
    ]
    return jsonify(poses)


@app.route('/api/admin/stats', methods=['GET'])
@login_required
def get_stats(user):
    """获取系统统计"""
    if user.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    stats = db.get_system_overview()
    return jsonify({
        'total_assessments': stats.get('total_assessments', 0),
        'avg_score': stats.get('average_score', 0),
        'total_users': stats.get('total_users', 0),
        'today_assessments': stats.get('today_assessments', 0),
        'active_users': stats.get('active_users', 0),
        'pose_types': stats.get('pose_types', 0)
    })


@app.route('/api/assessment/upload', methods=['POST'])
@login_required
def upload_video(user):
    """上传视频并进行评估"""
    global next_assessment_id
    
    try:
        # 获取表单数据
        if 'video' not in request.files:
            return jsonify({'error': '未上传视频文件'}), 400
        
        video_file = request.files['video']
        pose_name = request.form.get('pose_name', 'Mountain Pose')
        
        if video_file.filename == '':
            return jsonify({'error': '文件为空'}), 400
        
        # 保存视频
        with assessment_lock:
            assessment_id = next_assessment_id
            next_assessment_id += 1
        video_path = (UPLOAD_DIR / f"video_{assessment_id}_{video_file.filename}").resolve()
        video_file.save(str(video_path))
        
        # 创建评估记录
        assessments[assessment_id] = {
            'id': assessment_id,
            'user_id': user['id'],
            'video_path': str(video_path),
            'pose_name': pose_name,
            'status': 'processing',
            'timestamp': datetime.now().isoformat(),
            'result': None,
            'db_record_id': None
        }
        
        # 后台处理视频
        worker = threading.Thread(
            target=process_assessment_task,
            args=(assessment_id, dict(user), video_path, video_file.filename, pose_name, request.remote_addr),
            daemon=True
        )
        worker.start()

        return jsonify({
            'id': assessment_id,
            'status': 'processing'
        }), 202

        try:
            print(f"开始处理视频: {video_path} (姿态: {pose_name})")
            start_time = time.time()
            
            # 1. 读取视频
            video_info, frames = video_reader.read(str(video_path))
            print(f"读取成功: {len(frames)} 帧")
            
            # 2. 关键点检测
            print("检测关键点...")
            landmarks_seq = pose_detector.detect_sequence(frames)
            
            # 过滤无效帧
            valid_landmarks = [lm for lm in landmarks_seq if lm is not None]
            if not valid_landmarks:
                assessments[assessment_id]['status'] = 'failed'
                assessments[assessment_id]['result'] = {'error': '未检测到人体关键点'}
                print(f"评估失败: 无法检测关键点")
                return jsonify({
                    'id': assessment_id,
                    'status': 'failed',
                    'error': '未检测到人体关键点'
                })
            
            # 3. 角度计算
            print("计算角度...")
            angles_seq = angle_calculator.compute_all(landmarks_seq)
            
            # 4. 统计分析
            print("分析统计...")
            stats = stats_calculator.compute(angles_seq)
            stability_score = stats_calculator.compute_stability(landmarks_seq)
            
            # 5. 构建提示词
            pose_standard = POSE_STANDARDS.get(pose_name)
            prompt = prompt_builder.build(stats, stability_score, pose_name, pose_standard)
            
            # 6. 调用多模态 API 或使用简化评估
            assessment_result = None
            if multimodal_available:
                try:
                    print("调用多模态 API...")
                    middle_idx = len(frames) // 2
                    key_frame = frames[middle_idx]
                    
                    # 使用多模态 API 分析关键帧
                    model_response = multimodal_client.analyze_image_with_prompt(key_frame, prompt)
                    print(f"多模态 API 返回内容长度: {len(model_response)} 字符")
                    
                    assessment_result = result_parser.parse(model_response)
                    
                    if not assessment_result.get('success', False):
                        print("多模态 API 解析失败，使用简化评估...")
                        assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
                except Exception as e:
                    print(f"多模态 API 调用异常: {e}，使用简化评估...")
                    assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
            elif ollama_available:
                try:
                    print("调用 Ollama 模型（后备方案）...")
                    middle_idx = len(frames) // 2
                    key_frame = frames[middle_idx]
                    model_response = ollama_client.generate(prompt, key_frame)
                    assessment_result = result_parser.parse(model_response)
                    
                    if not assessment_result.get('success', False):
                        print("大模型解析失败，使用简化评估...")
                        assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
                except Exception as e:
                    print(f"大模型调用异常: {e}，使用简化评估...")
                    assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
            else:
                print("Ollama不可用，使用简化评估...")
                assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
            
            # 7. 提取分数
            if assessment_result is None:
                print("警告: 评估结果为空，使用默认分数")
                result = {
                    'total_score': 75.0,
                    'structure_score': 45.0,
                    'alignment_score': 22.5,
                    'stability_score': 7.5,
                    'angle_data': stats,
                    'problems': ['无法获取详细评估'],
                    'suggestions': ['请尝试重新上传视频']
                }
            else:
                score_data = assessment_result.get('data', {}).get('score', {}) if assessment_result.get('data') else {}
                
                # 确保所有分数都是有效的数字
                total_score = score_data.get('total', 80) if score_data.get('total') is not None else 80
                structure_score = score_data.get('accuracy', 50) if score_data.get('accuracy') is not None else 50
                alignment_score = score_data.get('stability', 25) if score_data.get('stability') is not None else 25
                stability_score_val = score_data.get('coordination', 5) if score_data.get('coordination') is not None else 5
                
                # 获取问题和建议，确保是列表
                problems = assessment_result.get('data', {}).get('problems', []) if assessment_result.get('data') else []
                if not isinstance(problems, list):
                    problems = []
                    
                suggestions = assessment_result.get('data', {}).get('suggestions', []) if assessment_result.get('data') else []
                if not isinstance(suggestions, list):
                    suggestions = []
                
                result = {
                    'total_score': float(total_score),
                    'structure_score': float(structure_score),
                    'alignment_score': float(alignment_score),
                    'stability_score': float(stability_score_val),
                    'angle_data': stats,
                    'problems': problems,
                    'suggestions': suggestions
                }
            
            # 保存评估到数据库
            record_data = {
                'user_id': user['id'],
                'video_name': video_file.filename,
                'video_path': str(video_path),
                'pose_name': pose_name,
                'total_score': result['total_score'],
                'structure_score': result['structure_score'],
                'alignment_score': result['alignment_score'],
                'stability_score': result['stability_score'],
                'angle_data': stats,
                'graph_data': {},
                'stability_rating': stability_score,
                'problems': result['problems'],
                'suggestions': result['suggestions'],
                'annotated_video_path': None,
                'video_duration': video_info.get('duration') if isinstance(video_info, dict) else None,
                'video_fps': video_info.get('fps') if isinstance(video_info, dict) else None,
                'video_resolution': f"{video_info.get('width', 0)}x{video_info.get('height', 0)}" if isinstance(video_info, dict) else None,
                'frame_count': len(frames),
                'processing_time': round(time.time() - start_time, 2),
                'model_used': 'qwen' if multimodal_available else 'simple_evaluator'
            }
            assessments[assessment_id]['db_record_id'] = db.create_assessment_record(record_data)
            assessments[assessment_id]['status'] = 'completed'
            assessments[assessment_id]['result'] = result
            print(f"评估完成: ID={assessment_id}, 分数={result['total_score']}")
            
        except Exception as e:
            import traceback
            print(f"处理异常: {e}")
            print(traceback.format_exc())
            assessments[assessment_id]['status'] = 'failed'
            assessments[assessment_id]['result'] = {'error': str(e)}
        db.add_log('error', 'ERROR', 'assessment_failure', str(e), user_id=user['id'], ip_address=request.remote_addr)
        
        return jsonify({
            'id': assessment_id,
            'status': assessments[assessment_id]['status']
        })
    
    except Exception as e:
        print(f"上传失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/assessment/<int:assessment_id>', methods=['GET'])
@login_required
def get_assessment(user, assessment_id):
    """获取评估状态"""
    if assessment_id not in assessments:
        return jsonify({'error': '评估不存在'}), 404

    assessment = assessments[assessment_id]
    if assessment['user_id'] != user['id'] and user.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify({
        'id': assessment_id,
        'status': assessment['status'],
        'progress': 100 if assessment['status'] in ['completed', 'failed'] else 50,
        'result': assessment['result'] if assessment['status'] in ['completed', 'failed'] else None
    })


@app.route('/api/assessment/<int:assessment_id>/result', methods=['GET'])
@login_required
def get_assessment_result(user, assessment_id):
    """获取评估详细结果"""
    if assessment_id not in assessments:
        return jsonify({'error': '评估不存在'}), 404

    assessment = assessments[assessment_id]
    if assessment['user_id'] != user['id'] and user.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403

    if assessment['status'] != 'completed':
        return jsonify({'error': '评估未完成'}), 400

    return jsonify(assessment['result'])


def main():
    """启动应用"""
    print("\n" + "="*50)
    print("启动 Python Flask REST API 后端")
    print("地址: http://localhost:5000")
    print("API前缀: /api")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()
