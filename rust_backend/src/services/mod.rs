//! Services Module
//! Business logic and core services

pub mod pose_analyzer;
pub mod ollama_client;
pub mod video_processor;

pub use pose_analyzer::PoseAnalyzer;
pub use ollama_client::OllamaClient;
pub use video_processor::VideoProcessor;
