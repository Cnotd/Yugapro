// Pose analyzer service - Simplified version
// Uses Python MediaPipe for pose detection

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseKeypoint {
    pub name: String,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub visibility: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseData {
    pub keypoints: Vec<PoseKeypoint>,
    pub total_visibility: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AngleData {
    pub left_elbow: f32,
    pub right_elbow: f32,
    pub left_knee: f32,
    pub right_knee: f32,
    pub left_hip: f32,
    pub right_hip: f32,
    pub spine: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphEdge {
    pub from: usize,
    pub to: usize,
    pub distance: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseGraph {
    pub keypoints: Vec<PoseKeypoint>,
    pub edges: Vec<GraphEdge>,
    pub angles: AngleData,
}

#[derive(Clone)]
pub struct PoseAnalyzer {
    python_path: String,
    mediapipe_script: String,
}

impl PoseAnalyzer {
    pub fn new() -> Result<Self> {
        Ok(Self {
            python_path: "python".to_string(),
            mediapipe_script: "src/pose_detection.py".to_string(),
        })
    }

    pub fn with_config(python_path: &str, script_path: &str) -> Result<Self> {
        Ok(Self {
            python_path: python_path.to_string(),
            mediapipe_script: script_path.to_string(),
        })
    }

    /// Detect pose from image using MediaPipe
    pub async fn detect_pose(&self, image_path: &str) -> Result<PoseData> {
        let script = format!(r#"
import cv2
import mediapipe as mp
import json
import sys

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, model_complexity=2)

image = cv2.imread("{}")
if image is None:
    print('{{"error": "Cannot read image"}}')
    sys.exit(1)

image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
results = pose.process(image_rgb)

if not results.pose_landmarks:
    print('{{"error": "No pose detected"}}')
    sys.exit(1)

keypoints = []
total_visibility = 0.0

landmarks_to_check = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index"
]

for idx, landmark in enumerate(results.pose_landmarks.landmark):
    name = landmarks_to_check[idx] if idx < len(landmarks_to_check) else f"landmark_{{idx}}"
    keypoints.append({{
        "name": name,
        "x": landmark.x,
        "y": landmark.y,
        "z": landmark.z,
        "visibility": landmark.visibility
    }})
    total_visibility += landmark.visibility

pose.close()

print(json.dumps({{
    "keypoints": keypoints,
    "total_visibility": total_visibility / len(keypoints)
}}))
"#, image_path.replace('\\', "\\\\").replace('"', "\\\""));

        let output = Command::new(&self.python_path)
            .args(&["-c", &script])
            .output()?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        
        if stdout.contains("error") {
            anyhow::bail!("Pose detection failed: {}", stdout);
        }

        let pose_data: PoseData = serde_json::from_str(&stdout)?;
        Ok(pose_data)
    }

    /// Calculate joint angles
    pub fn calculate_angles(&self, keypoints: &[PoseKeypoint]) -> AngleData {
        fn calculate_angle(p1: &[f32], p2: &[f32], p3: &[f32]) -> f32 {
            let v1 = [p1[0] - p2[0], p1[1] - p2[1]];
            let v2 = [p3[0] - p2[0], p3[1] - p2[1]];
            
            let dot = v1[0] * v2[0] + v1[1] * v2[1];
            let mag1 = (v1[0] * v1[0] + v1[1] * v1[1]).sqrt();
            let mag2 = (v2[0] * v2[0] + v2[1] * v2[1]).sqrt();
            
            if mag1 == 0.0 || mag2 == 0.0 {
                return 0.0;
            }
            
            let cos_angle = (dot / (mag1 * mag2)).clamp(-1.0, 1.0);
            cos_angle.acos().to_degrees()
        }

        let get_point = |name: &str| -> [f32; 3] {
            keypoints.iter()
                .find(|k| k.name == name)
                .map(|k| [k.x, k.y, k.z])
                .unwrap_or([0.0, 0.0, 0.0])
        };

        // Calculate angles
        let left_shoulder = get_point("left_shoulder");
        let right_shoulder = get_point("right_shoulder");
        let left_elbow = get_point("left_elbow");
        let right_elbow = get_point("right_elbow");
        let left_wrist = get_point("left_wrist");
        let right_wrist = get_point("right_wrist");
        let left_hip = get_point("left_hip");
        let right_hip = get_point("right_hip");
        let left_knee = get_point("left_knee");
        let right_knee = get_point("right_knee");
        let left_ankle = get_point("left_ankle");
        let right_ankle = get_point("right_ankle");

        AngleData {
            left_elbow: calculate_angle(&left_shoulder, &left_elbow, &left_wrist),
            right_elbow: calculate_angle(&right_shoulder, &right_elbow, &right_wrist),
            left_knee: calculate_angle(&left_hip, &left_knee, &left_ankle),
            right_knee: calculate_angle(&right_hip, &right_knee, &right_ankle),
            left_hip: calculate_angle(&left_shoulder, &left_hip, &left_knee),
            right_hip: calculate_angle(&right_shoulder, &right_hip, &right_knee),
            spine: calculate_angle(&left_shoulder, &[(left_shoulder[0] + right_shoulder[0]) / 2.0, (left_shoulder[1] + right_shoulder[1]) / 2.0, 0.0], 
                                   &[(left_hip[0] + right_hip[0]) / 2.0, (left_hip[1] + right_hip[1]) / 2.0, 0.0]),
        }
    }

    /// Build pose graph from keypoints
    pub fn build_pose_graph(&self, keypoints: &[PoseKeypoint]) -> PoseGraph {
        // Standard body connections
        let connections = vec![
            // Face
            (0, 1), (1, 2), (2, 3), (3, 7),  // Left eye to ear
            (0, 4), (4, 5), (5, 6), (6, 8),  // Right eye to ear
            (9, 10),                         // Mouth
            // Upper body
            (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
            // Torso
            (11, 23), (12, 24), (23, 24),    // Shoulders to hips
            // Lower body
            (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
            (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
        ];

        let mut edges = Vec::new();
        
        for &(from, to) in &connections {
            if from < keypoints.len() && to < keypoints.len() {
                let p1 = &keypoints[from];
                let p2 = &keypoints[to];
                let distance = ((p1.x - p2.x).powi(2) + (p1.y - p2.y).powi(2) + (p1.z - p2.z).powi(2)).sqrt();
                
                edges.push(GraphEdge {
                    from,
                    to,
                    distance,
                });
            }
        }

        let angles = self.calculate_angles(keypoints);

        PoseGraph {
            keypoints: keypoints.to_vec(),
            edges,
            angles,
        }
    }

    /// Analyze pose quality
    pub fn analyze_quality(&self, pose_graph: &PoseGraph) -> HashMap<String, f32> {
        let mut scores = HashMap::new();
        
        // Calculate visibility score
        let avg_visibility: f32 = pose_graph.keypoints.iter()
            .map(|k| k.visibility)
            .sum::<f32>() / pose_graph.keypoints.len() as f32;
        scores.insert("visibility".to_string(), avg_visibility * 100.0);
        
        // Calculate angle scores
        let angle_score = |name: &str, ideal: f32, tolerance: f32| -> f32 {
            let angle = match name {
                "left_elbow" => pose_graph.angles.left_elbow,
                "right_elbow" => pose_graph.angles.right_elbow,
                "left_knee" => pose_graph.angles.left_knee,
                "right_knee" => pose_graph.angles.right_knee,
                "left_hip" => pose_graph.angles.left_hip,
                "right_hip" => pose_graph.angles.right_hip,
                _ => 0.0,
            };
            
            let diff = (angle - ideal).abs();
            if diff <= tolerance {
                100.0 - (diff / tolerance) * 50.0
            } else {
                50.0 - ((diff - tolerance) / tolerance) * 50.0
            }
        };
        
        scores.insert("left_elbow".to_string(), angle_score("left_elbow", 160.0, 20.0));
        scores.insert("right_elbow".to_string(), angle_score("right_elbow", 160.0, 20.0));
        scores.insert("left_knee".to_string(), angle_score("left_knee", 170.0, 15.0));
        scores.insert("right_knee".to_string(), angle_score("right_knee", 170.0, 15.0));
        
        scores
    }
}

impl Default for PoseAnalyzer {
    fn default() -> Self {
        Self::new().expect("Failed to create default PoseAnalyzer")
    }
}
