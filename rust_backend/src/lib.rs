//! Yoga Assessment API Library

pub mod api;
pub mod db;
pub mod models;
pub mod services;

use crate::db::Database;
use crate::services::pose_analyzer::PoseAnalyzer;

#[derive(Clone)]
pub struct AppState {
    pub db: Database,
    pub pose_analyzer: PoseAnalyzer,
}
