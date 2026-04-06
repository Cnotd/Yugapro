#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke test for auth, upload, and polling on the current API."""

import json
import os
import time
from pathlib import Path

import requests


API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:5000/api")
USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "admin123")
POLL_SECONDS = int(os.environ.get("API_POLL_SECONDS", "120"))


def find_video() -> Path:
    preferred = [
        Path("uploads") / "video_1_屏幕录制 2025-05-22 185837.mp4",
        Path("uploads") / "video_2_屏幕录制 2025-05-22 185837.mp4",
    ]
    for path in preferred:
        if path.exists():
            return path

    matches = []
    for pattern in ("uploads/*.mp4", "data/temp/*.mp4", "data/**/*.mp4"):
        matches.extend(Path(".").glob(pattern))

    if not matches:
        raise FileNotFoundError("No test video found")

    return sorted(matches, key=lambda item: item.stat().st_size)[0]


def main() -> int:
    print("=" * 60)
    print("API smoke test")
    print("=" * 60)

    video_path = find_video()
    print(f"Using video: {video_path}")

    session = requests.Session()

    response = session.get(f"{API_BASE}/health", timeout=5)
    print("health:", response.status_code, response.text[:160])
    response.raise_for_status()

    response = session.post(
        f"{API_BASE}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    print("login:", response.status_code, response.text[:200])
    response.raise_for_status()
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = session.get(f"{API_BASE}/auth/me", headers=headers, timeout=5)
    print("profile:", response.status_code, response.text[:160])
    response.raise_for_status()

    with video_path.open("rb") as video_file:
        response = session.post(
            f"{API_BASE}/assessment/upload",
            headers=headers,
            files={"video": (video_path.name, video_file, "video/mp4")},
            data={"pose_name": "Mountain Pose"},
            timeout=30,
        )
    print("upload:", response.status_code, response.text[:200])
    response.raise_for_status()
    upload_data = response.json()
    assessment_id = upload_data.get("id")
    if not assessment_id:
        raise RuntimeError(f"Upload response missing id: {upload_data}")

    deadline = time.time() + POLL_SECONDS
    payload = None
    while time.time() < deadline:
        response = session.get(
            f"{API_BASE}/assessment/{assessment_id}",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        print("poll:", payload.get("status"), payload.get("progress"))
        if payload.get("status") in {"completed", "failed"}:
            break
        time.sleep(2)

    if not payload:
        raise RuntimeError("No assessment payload returned")
    if payload.get("status") not in {"completed", "failed"}:
        raise TimeoutError(f"Assessment did not finish within {POLL_SECONDS}s")

    print(json.dumps(payload, ensure_ascii=False, indent=2)[:3000])

    result = payload.get("result") or {}
    if payload.get("status") == "completed":
        assert "total_score" in result
        assert "angle_data" in result
        assert isinstance(result.get("problems", []), list)
        assert isinstance(result.get("suggestions", []), list)
        print("completed successfully")
        return 0

    print("assessment failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
