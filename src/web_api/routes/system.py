"""Public health, stats, and pose-standard routes."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify


system_bp = Blueprint("system", __name__)


@system_bp.get("/health")
def health_check():
    context = current_app.config["YOGA_CONTEXT"]
    return jsonify(
        {
            "service": "yoga-assessment-api",
            "status": "ok",
            "version": "0.2.0",
            "backend": "Python Flask",
            "test_mode": context.test_mode,
        }
    )


@system_bp.get("/stats")
def public_stats():
    context = current_app.config["YOGA_CONTEXT"]
    stats = context.db.get_system_overview()
    return jsonify(
        {
            "total_assessments": stats.get("total_assessments", 0),
            "total_users": stats.get("total_users", 0),
            "avg_score": stats.get("average_score", 0),
            "pose_types": stats.get("pose_types", 0),
        }
    )


@system_bp.get("/pose/standards")
def get_pose_standards():
    return jsonify(
        [
            {
                "id": 1,
                "pose_name": "Mountain Pose",
                "pose_name_cn": "山式",
                "difficulty_level": "Beginner",
                "hip_min": 170.0,
                "hip_max": 180.0,
                "knee_min": 165.0,
                "knee_max": 180.0,
                "shoulder_min": 170.0,
                "shoulder_max": 180.0,
                "spine_min": 0.0,
                "spine_max": 10.0,
            },
            {
                "id": 2,
                "pose_name": "Tree Pose",
                "pose_name_cn": "树式",
                "difficulty_level": "Intermediate",
                "hip_min": 150.0,
                "hip_max": 175.0,
                "knee_min": 160.0,
                "knee_max": 180.0,
                "shoulder_min": 160.0,
                "shoulder_max": 180.0,
                "spine_min": 0.0,
                "spine_max": 15.0,
            },
            {
                "id": 3,
                "pose_name": "Warrior II",
                "pose_name_cn": "战士二式",
                "difficulty_level": "Intermediate",
                "hip_min": 140.0,
                "hip_max": 170.0,
                "knee_min": 155.0,
                "knee_max": 175.0,
                "shoulder_min": 160.0,
                "shoulder_max": 180.0,
                "spine_min": 0.0,
                "spine_max": 20.0,
            },
            {
                "id": 4,
                "pose_name": "Triangle Pose",
                "pose_name_cn": "三角式",
                "difficulty_level": "Intermediate",
                "hip_min": 150.0,
                "hip_max": 175.0,
                "knee_min": 160.0,
                "knee_max": 180.0,
                "shoulder_min": 155.0,
                "shoulder_max": 180.0,
                "spine_min": 5.0,
                "spine_max": 25.0,
            },
            {
                "id": 5,
                "pose_name": "Chair Pose",
                "pose_name_cn": "椅子式",
                "difficulty_level": "Beginner",
                "hip_min": 130.0,
                "hip_max": 160.0,
                "knee_min": 150.0,
                "knee_max": 175.0,
                "shoulder_min": 165.0,
                "shoulder_max": 180.0,
                "spine_min": 0.0,
                "spine_max": 15.0,
            },
            {
                "id": 6,
                "pose_name": "Half Moon Pose",
                "pose_name_cn": "半月式",
                "difficulty_level": "Intermediate",
                "hip_min": 155.0,
                "hip_max": 180.0,
                "knee_min": 165.0,
                "knee_max": 180.0,
                "shoulder_min": 160.0,
                "shoulder_max": 180.0,
                "spine_min": 0.0,
                "spine_max": 20.0,
            },
        ]
    )
