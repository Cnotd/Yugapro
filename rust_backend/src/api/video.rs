//! Video API endpoints

use axum::{
    extract::Path,
    http::{HeaderValue, StatusCode},
    response::{IntoResponse, Response},
};
use std::path::PathBuf;

pub async fn get_video(Path(video_id): Path<String>) -> Response {
    let video_path = format!("uploads/{}.mp4", video_id);
    let path = PathBuf::from(&video_path);
    
    if !path.exists() {
        return (StatusCode::NOT_FOUND, "Video not found").into_response();
    }
    
    // Read video file and return as response
    match tokio::fs::read(&path).await {
        Ok(data) => {
            let mut response = data.into_response();
            *response.status_mut() = StatusCode::OK;
            response.headers_mut().insert(
                "Content-Type",
                HeaderValue::from_static("video/mp4"),
            );
            response
        }
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to read video").into_response(),
    }
}

pub async fn get_annotated_video(Path(video_id): Path<String>) -> Response {
    // For now, return not found - annotated video generation not implemented
    let annotated_path = format!("uploads/{}_annotated.mp4", video_id);
    let path = PathBuf::from(&annotated_path);
    
    if !path.exists() {
        return (StatusCode::NOT_FOUND, "Annotated video not found").into_response();
    }
    
    match tokio::fs::read(&path).await {
        Ok(data) => {
            let mut response = data.into_response();
            *response.status_mut() = StatusCode::OK;
            response.headers_mut().insert(
                "Content-Type",
                HeaderValue::from_static("video/mp4"),
            );
            response
        }
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to read video").into_response(),
    }
}
