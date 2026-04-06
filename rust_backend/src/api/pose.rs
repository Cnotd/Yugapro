//! Pose API endpoints

use axum::{
    extract::{Path, State},
    Json,
};

use crate::AppState;
use crate::db::PoseStandard;

pub async fn list_standards(
    State(state): State<AppState>,
) -> Json<Vec<PoseStandard>> {
    let standards: Vec<PoseStandard> = state.db
        .list_pose_standards()
        .await
        .unwrap_or_default();
    Json(standards)
}

pub async fn get_standard(
    State(state): State<AppState>,
    Path(pose_name): Path<String>,
) -> Json<Option<PoseStandard>> {
    let standard: Option<PoseStandard> = state.db
        .get_pose_standard(&pose_name)
        .await
        .unwrap_or_default();
    Json(standard)
}
