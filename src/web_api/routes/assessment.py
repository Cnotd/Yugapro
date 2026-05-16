"""Assessment upload, polling, and result routes."""

from __future__ import annotations

import threading
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from src.web_api.context import ApiContext
from src.web_api.security import login_required


assessment_bp = Blueprint("assessment", __name__)


@assessment_bp.post("/upload")
@login_required
def upload_video(user):
    context: ApiContext = current_app.config["YOGA_CONTEXT"]

    # 上传接口只负责校验、保存文件和创建任务，耗时分析交给后台线程。
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file = request.files["video"]
    pose_name = request.form.get("pose_name", "Mountain Pose").strip() or "Mountain Pose"

    task = context.task_manager.create(
        user_id=user["id"],
        video_path="",
        pose_name=pose_name,
    )

    try:
        saved_path = context.upload_storage.save_video(video_file, task.id)
        context.task_manager.update(task.id, progress=10)
        task.video_path = str(saved_path)
    except Exception as exc:
        context.task_manager.update(task.id, status="failed", progress=100, result={"error": str(exc)}, error=str(exc))
        return jsonify({"error": str(exc)}), 400

    worker = threading.Thread(
        target=_run_assessment_worker,
        args=(context, task.id, dict(user), saved_path, video_file.filename or saved_path.name, pose_name, request.remote_addr),
        daemon=True,
    )
    # 后台线程启动后立即返回 202，前端通过任务 id 轮询状态。
    worker.start()

    return jsonify({"id": task.id, "assessment_id": task.id, "status": "processing"}), 202


@assessment_bp.get("/<int:assessment_id>")
@login_required
def get_assessment(user, assessment_id):
    context: ApiContext = current_app.config["YOGA_CONTEXT"]
    task = context.task_manager.get(assessment_id)
    if not task:
        return jsonify({"error": "Assessment does not exist"}), 404
    if task.user_id != user["id"] and user.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    # 普通用户只能查看自己的任务，管理员用于后台排查时可查看全部任务。
    return jsonify(task.to_response())


@assessment_bp.get("/<int:assessment_id>/result")
@login_required
def get_assessment_result(user, assessment_id):
    context: ApiContext = current_app.config["YOGA_CONTEXT"]
    task = context.task_manager.get(assessment_id)
    if not task:
        return jsonify({"error": "Assessment does not exist"}), 404
    if task.user_id != user["id"] and user.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    if task.status != "completed":
        return jsonify({"error": "Assessment has not completed"}), 400
    return jsonify(task.result or {})


def _run_assessment_worker(
    context: ApiContext,
    task_id: int,
    user: dict,
    video_path: Path,
    video_filename: str,
    pose_name: str,
    remote_addr: str | None,
) -> None:
    try:
        context.task_manager.update(task_id, status="processing", progress=20)
        # 这里是完整评估主流程，内部会完成视频读取、姿态分析、模型反馈和兜底评估。
        result = context.assessment_pipeline.run(
            user_id=user["id"],
            video_path=video_path,
            original_filename=video_filename,
            pose_name=pose_name,
        )
        context.task_manager.update(task_id, progress=85)
        # 先落库再标记完成，保证前端看到 completed 时历史记录也已经可查询。
        record_id = context.db.create_assessment_record(result.record_data)
        context.task_manager.update(
            task_id,
            status="completed",
            progress=100,
            result=result.api_result,
            db_record_id=record_id,
        )
    except Exception as exc:
        message = str(exc)
        # 任何异常都要写回任务状态，避免前端一直停留在“处理中”。
        context.task_manager.update(
            task_id,
            status="failed",
            progress=100,
            result={"error": message},
            error=message,
        )
        try:
            context.db.add_log(
                "error",
                "ERROR",
                "assessment_failure",
                message,
                user_id=user.get("id"),
                ip_address=remote_addr,
            )
        except Exception:
            pass
