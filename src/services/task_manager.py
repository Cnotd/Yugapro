"""Thread-safe in-memory task registry for assessment jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional


TERMINAL_STATUSES = {"completed", "failed"}


@dataclass
class AssessmentTask:
    # 任务对象只保存在当前进程内，用于前端轮询查看处理进度。
    id: int
    user_id: int
    video_path: str
    pose_name: str
    status: str = "processing"
    progress: int = 5
    result: Optional[Dict[str, Any]] = None
    db_record_id: Optional[int] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_response(self, include_result: bool = True) -> Dict[str, Any]:
        # 未完成时不返回 result，避免前端拿到半成品数据误渲染。
        payload = {
            "id": self.id,
            "user_id": self.user_id,
            "pose_name": self.pose_name,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_result:
            payload["result"] = self.result if self.status in TERMINAL_STATUSES else None
        if self.error:
            payload["error"] = self.error
        if self.db_record_id:
            payload["db_record_id"] = self.db_record_id
        return payload


class TaskManager:
    """Small process-local task store used by the Flask worker threads."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._next_id = 1
        self._tasks: Dict[int, AssessmentTask] = {}

    def create(self, user_id: int, video_path: str, pose_name: str) -> AssessmentTask:
        # 多个上传请求可能并发到达，任务编号和字典写入必须加锁。
        with self._lock:
            task_id = self._next_id
            self._next_id += 1
            task = AssessmentTask(
                id=task_id,
                user_id=user_id,
                video_path=video_path,
                pose_name=pose_name,
            )
            self._tasks[task_id] = task
            return task

    def get(self, task_id: int) -> Optional[AssessmentTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def update(
        self,
        task_id: int,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        db_record_id: Optional[int] = None,
    ) -> Optional[AssessmentTask]:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            # update 支持局部更新，后台线程可以只推进状态或只写入结果。
            if status is not None:
                task.status = status
            if progress is not None:
                # 进度统一限制在 0-100，避免异常值影响前端进度条。
                task.progress = max(0, min(100, int(progress)))
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if db_record_id is not None:
                task.db_record_id = db_record_id
            task.updated_at = datetime.now().isoformat()
            return task

    def clear(self) -> None:
        with self._lock:
            self._tasks.clear()
            self._next_id = 1
