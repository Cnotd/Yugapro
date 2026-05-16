"""Upload storage helpers for the Flask API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


DEFAULT_ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}


class UploadStorage:
    """Save user-uploaded videos under a date-partitioned directory."""

    def __init__(
        self,
        root: Path,
        allowed_extensions: Iterable[str] = DEFAULT_ALLOWED_EXTENSIONS,
        max_size_mb: int = 200,
    ) -> None:
        self.root = Path(root)
        self.allowed_extensions = {item.lower() for item in allowed_extensions}
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.root.mkdir(parents=True, exist_ok=True)

    def save_video(self, file: FileStorage, task_id: int) -> Path:
        if not file or not file.filename:
            raise ValueError("No video file uploaded")

        source_name = secure_filename(file.filename) or "video.mp4"
        suffix = Path(source_name).suffix.lower()
        if suffix not in self.allowed_extensions:
            allowed = ", ".join(sorted(self.allowed_extensions))
            raise ValueError(f"Unsupported video format: {suffix}. Allowed: {allowed}")

        if self._content_length(file) > self.max_size_bytes:
            limit_mb = self.max_size_bytes // (1024 * 1024)
            raise ValueError(f"Video file is larger than {limit_mb}MB")

        day_dir = self.root / datetime.now().strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)

        target = day_dir / f"task_{task_id}_{source_name}"
        file.save(str(target))

        if target.stat().st_size > self.max_size_bytes:
            target.unlink(missing_ok=True)
            limit_mb = self.max_size_bytes // (1024 * 1024)
            raise ValueError(f"Video file is larger than {limit_mb}MB")

        return target.resolve()

    @staticmethod
    def _content_length(file: FileStorage) -> int:
        length = file.content_length
        if length is not None:
            return length
        try:
            stream = file.stream
            current = stream.tell()
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(current)
            return size
        except Exception:
            return 0
