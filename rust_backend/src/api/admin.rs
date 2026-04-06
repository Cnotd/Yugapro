//! Admin API endpoints

use axum::{
    extract::State,
    Json,
};

use crate::AppState;
use crate::db::{SystemStats, User};

pub async fn get_stats(
    State(state): State<AppState>,
) -> Json<SystemStats> {
    let stats: SystemStats = state.db.get_stats().await.unwrap_or(SystemStats {
        total_assessments: 0,
        total_users: 0,
        avg_score: 0.0,
        today_assessments: 0,
    });
    Json(stats)
}

pub async fn list_users(
    State(state): State<AppState>,
) -> Json<Vec<User>> {
    let users: Vec<User> = state.db.list_users().await.unwrap_or_default();
    Json(users)
}
