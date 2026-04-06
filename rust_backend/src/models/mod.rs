//! Data Models
//! Core data structures for the yoga assessment system

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// User model
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub email: Option<String>,
    pub role: String,
    pub created_at: DateTime<Utc>,
    pub last_login: Option<DateTime<Utc>>,
    pub is_active: bool,
}

/// Assessment record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssessmentRecord {
    pub id: i64,
    pub user_id: i64,
    pub video_name: String,
    pub video_path: String,
    pub pose_name: String,
    pub assessment_time: DateTime<Utc>,
    pub total_score: Option<f64>,
    pub structure_score: Option<f64>,
    pub alignment_score: Option<f64>,
    pub stability_score: Option<f64>,
    pub angle_data: Option<String>,
    pub graph_data: Option<String>,
    pub problems: Option<String>,
    pub suggestions: Option<String>,
    pub annotated_video_path: Option<String>,
    pub processing_time: Option<f64>,
    pub model_used: Option<String>,
}

/// Video data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VideoData {
    pub id: i64,
    pub user_id: i64,
    pub video_name: String,
    pub file_path: String,
    pub file_size: i64,
    pub file_format: String,
    pub video_duration: Option<f64>,
    pub video_fps: Option<f64>,
    pub video_width: Option<i32>,
    pub video_height: Option<i32>,
    pub upload_time: DateTime<Utc>,
    pub processing_status: String,
}

/// Pose standard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseStandard {
    pub id: i64,
    pub pose_name: String,
    pub pose_name_en: Option<String>,
    pub category: Option<String>,
    pub difficulty_level: Option<String>,
    pub hip_min: Option<f64>,
    pub hip_max: Option<f64>,
    pub knee_min: Option<f64>,
    pub knee_max: Option<f64>,
    pub shoulder_min: Option<f64>,
    pub shoulder_max: Option<f64>,
    pub spine_min: Option<f64>,
    pub spine_max: Option<f64>,
    pub description: Option<String>,
    pub common_errors: Option<String>,
}

/// Pose landmark (33 MediaPipe keypoints)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseLandmark {
    pub id: usize,
    pub name: String,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub visibility: f64,
}

/// Pose graph representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseGraph {
    pub nodes: Vec<PoseNode>,
    pub edges: Vec<PoseEdge>,
    pub stats: GraphStats,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseNode {
    pub id: usize,
    pub name: String,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub visibility: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseEdge {
    pub from_id: usize,
    pub to_id: usize,
    pub from_name: String,
    pub to_name: String,
    pub distance_3d: f64,
    pub distance_2d: f64,
    pub angle: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphStats {
    pub num_nodes: usize,
    pub num_edges: usize,
    pub avg_visibility: f64,
    pub max_distance: f64,
    pub min_distance: f64,
    pub avg_distance: f64,
}

/// Angle data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AngleData {
    pub left_elbow: Option<f64>,
    pub right_elbow: Option<f64>,
    pub left_knee: Option<f64>,
    pub right_knee: Option<f64>,
    pub left_hip: Option<f64>,
    pub right_hip: Option<f64>,
    pub left_shoulder: Option<f64>,
    pub right_shoulder: Option<f64>,
    pub spine_angle: Option<f64>,
    pub body_tilt: Option<f64>,
}

/// Assessment result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssessmentResult {
    pub total_score: f64,
    pub structure_score: f64,
    pub alignment_score: f64,
    pub stability_score: f64,
    pub problems: Vec<String>,
    pub suggestions: Vec<String>,
    pub angle_data: AngleData,
    pub graph_data: PoseGraph,
    pub model_response: String,
}

/// API Request/Response models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UploadResponse {
    pub video_id: i64,
    pub assessment_id: i64,
    pub status: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssessmentStatusResponse {
    pub assessment_id: i64,
    pub status: String,
    pub progress: f64,
    pub result: Option<AssessmentResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatsResponse {
    pub total_users: i64,
    pub total_assessments: i64,
    pub today_assessments: i64,
    pub average_score: f64,
    pub pose_types: i64,
    pub active_users: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: String,
    pub code: String,
    pub message: String,
}
