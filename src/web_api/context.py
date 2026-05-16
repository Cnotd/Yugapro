"""Application context shared by Flask route modules."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.database import DatabaseManager
from src.services.assessment_pipeline import AssessmentPipeline
from src.services.file_storage import UploadStorage
from src.services.task_manager import TaskManager


def truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class ApiContext:
    db: DatabaseManager
    task_manager: TaskManager
    upload_storage: UploadStorage
    assessment_pipeline: AssessmentPipeline
    test_mode: bool = False


def build_context(project_root: Path | None = None) -> ApiContext:
    root = project_root or Path(__file__).resolve().parents[2]
    test_mode = truthy_env("YOGA_TEST_MODE")
    db = DatabaseManager()
    return ApiContext(
        db=db,
        task_manager=TaskManager(),
        upload_storage=UploadStorage(root / "uploads"),
        assessment_pipeline=AssessmentPipeline(test_mode=test_mode),
        test_mode=test_mode,
    )
