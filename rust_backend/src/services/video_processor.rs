// Video processing service - Simplified version using Python subprocess
// This version calls Python scripts for actual video processing

use anyhow::Result;
use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VideoInfo {
    pub fps: f64,
    pub frame_count: u64,
    pub duration: f64,
    pub width: u32,
    pub height: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessedFrame {
    pub frame_id: u32,
    pub landmarks: Vec<Landmark>,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Landmark {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub visibility: f32,
}

pub struct VideoProcessor {
    python_path: String,
}

impl VideoProcessor {
    pub fn new() -> Self {
        Self {
            python_path: "python".to_string(),
        }
    }

    pub fn with_python_path(python_path: &str) -> Self {
        Self {
            python_path: python_path.to_string(),
        }
    }

    /// Get video information
    pub async fn get_video_info(&self, video_path: &str) -> Result<VideoInfo> {
        // Call Python script to get video info
        let output = Command::new(&self.python_path)
            .args(&[
                "-c",
                &format!(r#"
import cv2
import json
cap = cv2.VideoCapture("{}")
if cap.isOpened():
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    print(json.dumps({{"fps": fps, "frame_count": frame_count, "duration": duration, "width": width, "height": height}}))
    cap.release()
else:
    print('{{"error": "Cannot open video"}}')
"#, video_path.replace('\\', "\\\\").replace('"', "\\\""))
            ])
            .output()?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        
        if stdout.contains("error") {
            anyhow::bail!("Failed to get video info: {}", stdout);
        }

        let info: VideoInfo = serde_json::from_str(&stdout)?;
        Ok(info)
    }

    /// Sample frames uniformly from video
    pub async fn sample_frames(&self, video_path: &str, num_samples: u32) -> Result<Vec<String>> {
        // Create a temporary Python script for frame sampling
        let script = format!(r#"
import cv2
import os
import tempfile
import json

video_path = "{}"
num_samples = {}

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print('{{"error": "Cannot open video"}}')
    exit()

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Calculate sampling interval
interval = max(1, total_frames // num_samples)

frames = []
temp_dir = tempfile.mkdtemp()

for i in range(num_samples):
    frame_idx = i * interval
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        frame_path = os.path.join(temp_dir, f"frame_{{i}}.jpg")
        cv2.imwrite(frame_path, frame)
        frames.append(frame_path)

cap.release()
print(json.dumps({{"frames": frames, "temp_dir": temp_dir}}))
"#, 
            video_path.replace('\\', "\\\\").replace('"', "\\\""),
            num_samples
        );

        let output = Command::new(&self.python_path)
            .args(&["-c", &script])
            .output()?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        
        if stdout.contains("error") {
            anyhow::bail!("Failed to sample frames: {}", stdout);
        }

        let result: serde_json::Value = serde_json::from_str(&stdout)?;
        let frames: Vec<String> = serde_json::from_value(result["frames"].clone())?;
        
        Ok(frames)
    }

    /// Process a single frame to extract pose landmarks
    pub async fn process_frame(&self, frame_path: &str, script_path: &str) -> Result<ProcessedFrame> {
        let output = Command::new(&self.python_path)
            .arg(script_path)
            .arg(frame_path)
            .output()?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        
        if !output.status.success() {
            anyhow::bail!("Frame processing failed: {}", stdout);
        }

        let frame: ProcessedFrame = serde_json::from_str(&stdout)?;
        Ok(frame)
    }

    /// Batch process multiple frames
    pub async fn batch_process_frames(&self, frame_paths: &[String], script_path: &str) -> Result<Vec<ProcessedFrame>> {
        let mut results = Vec::new();
        
        for frame_path in frame_paths {
            match self.process_frame(frame_path, script_path).await {
                Ok(frame) => results.push(frame),
                Err(e) => tracing::warn!("Failed to process frame {}: {}", frame_path, e),
            }
        }

        Ok(results)
    }
}

impl Default for VideoProcessor {
    fn default() -> Self {
        Self::new()
    }
}
