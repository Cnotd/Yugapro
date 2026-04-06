//! Yoga Assessment API Server
//! High-performance Rust backend for yoga pose assessment

mod api;
mod db;
mod models;
mod services;

use anyhow::Result;
use axum::Router;
use tower_http::cors::{CorsLayer, Any};

use api::{health, assessment, video, pose, admin};
use db::Database;
use services::pose_analyzer::PoseAnalyzer;

#[derive(Clone)]
pub struct AppState {
    pub db: Database,
    pub pose_analyzer: PoseAnalyzer,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("===========================================");
    println!("  Yoga Assessment API Server Starting...");
    println!("===========================================");

    // 确保目录存在
    std::fs::create_dir_all("data")?;
    std::fs::create_dir_all("uploads")?;

    // 初始化数据库
    let db = Database::new("data/yoga_assessment.db").await?;
    println!("[OK] Database initialized");

    // 初始化姿态分析器
    let pose_analyzer = PoseAnalyzer::new()?;
    println!("[OK] Pose analyzer initialized");

    // 创建应用状态
    let state = AppState {
        db,
        pose_analyzer,
    };

    // 配置CORS - 允许所有来源、所有方法和所有头部
    let cors = CorsLayer::new()
        .allow_origin(Any)  // 允许所有来源
        .allow_methods(Any)  // 允许所有方法
        .allow_headers(Any); // 允许所有头部

    // 构建路由
    let app = Router::new()
        // 健康检查
        .route("/api/health", axum::routing::get(health::health_check))
        // 评估接口
        .route("/api/assessment/upload", axum::routing::post(assessment::upload_video))
        .route("/api/assessment/:id", axum::routing::get(assessment::get_assessment))
        .route("/api/assessment/:id/result", axum::routing::get(assessment::get_result))
        .route("/api/assessments", axum::routing::get(assessment::list_assessments))
        // 视频接口
        .route("/api/video/:id", axum::routing::get(video::get_video))
        .route("/api/video/:id/annotated", axum::routing::get(video::get_annotated_video))
        // 动作标准接口
        .route("/api/pose/standards", axum::routing::get(pose::list_standards))
        .route("/api/pose/standards/:name", axum::routing::get(pose::get_standard))
        // 管理接口
        .route("/api/admin/stats", axum::routing::get(admin::get_stats))
        .route("/api/admin/users", axum::routing::get(admin::list_users))
        // 中间件
        .layer(cors)
        .with_state(state);

    // 启动服务器
    let addr = "0.0.0.0:8080";
    println!("===========================================");
    println!("  Server listening on http://{}", addr);
    println!("  CORS: Enabled for all origins");
    println!("  API Endpoints:");
    println!("    - GET  /api/health");
    println!("    - POST /api/assessment/upload");
    println!("    - GET  /api/assessment/:id");
    println!("    - GET  /api/assessment/:id/result");
    println!("    - GET  /api/pose/standards");
    println!("    - GET  /api/admin/stats");
    println!("===========================================");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
