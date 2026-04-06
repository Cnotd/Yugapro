//! Health check API endpoint

use axum::Json;

pub async fn health_check() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "ok",
        "version": "0.1.0",
        "service": "yoga-assessment-api",
    }))
}
