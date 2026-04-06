//! Ollama Client Service
//! Interface with Ollama LLM API

use anyhow::{Result, anyhow};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;

use crate::models::{PoseGraph, AngleData, AssessmentResult};

#[derive(Debug, Serialize)]
struct OllamaRequest {
    model: String,
    prompt: String,
    images: Option<Vec<String>>,
    stream: bool,
    options: OllamaOptions,
}

#[derive(Debug, Serialize)]
struct OllamaOptions {
    temperature: f64,
    top_p: f64,
    num_predict: i32,
}

#[derive(Debug, Deserialize)]
struct OllamaResponse {
    model: String,
    response: String,
    done: bool,
}

#[derive(Debug, Deserialize)]
struct OllamaTagsResponse {
    models: Vec<OllamaModel>,
}

#[derive(Debug, Deserialize)]
struct OllamaModel {
    name: String,
    model: String,
    size: i64,
}

pub struct OllamaClient {
    client: Client,
    base_url: String,
    model: String,
}

impl OllamaClient {
    /// Create new Ollama client
    pub fn new(base_url: &str, model: &str) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(120))
            .build()
            .unwrap_or_default();

        Self {
            client,
            base_url: base_url.to_string(),
            model: model.to_string(),
        }
    }

    /// Check if Ollama is available
    pub async fn is_available(&self) -> bool {
        self.client
            .get(format!("{}/api/tags", self.base_url))
            .send()
            .await
            .is_ok()
    }

    /// List available models
    pub async fn list_models(&self) -> Result<Vec<String>> {
        let response = self.client
            .get(format!("{}/api/tags", self.base_url))
            .send()
            .await?
            .json::<OllamaTagsResponse>()
            .await?;

        Ok(response.models.into_iter().map(|m| m.name).collect())
    }

    /// Generate response from Ollama
    pub async fn generate(&self, prompt: &str, image_base64: Option<&str>) -> Result<String> {
        let request = OllamaRequest {
            model: self.model.clone(),
            prompt: prompt.to_string(),
            images: image_base64.map(|img| vec![img.to_string()]),
            stream: false,
            options: OllamaOptions {
                temperature: 0.7,
                top_p: 0.9,
                num_predict: 1024,
            },
        };

        let response = self.client
            .post(format!("{}/api/generate", self.base_url))
            .json(&request)
            .send()
            .await?
            .json::<OllamaResponse>()
            .await?;

        Ok(response.response)
    }

    /// Generate assessment result from pose data
    pub async fn assess_pose(&self, pose_name: &str, angle_data: &AngleData,
                             graph: &PoseGraph, stability_score: f64) -> Result<AssessmentResult> {
        let prompt = self.build_assessment_prompt(pose_name, angle_data, graph, stability_score);
        let response = self.generate(&prompt, None).await?;

        // Parse the response to extract structured result
        self.parse_assessment_response(&response, angle_data, graph, stability_score)
    }

    /// Build assessment prompt
    fn build_assessment_prompt(&self, pose_name: &str, angle_data: &AngleData,
                              graph: &PoseGraph, stability_score: f64) -> String {
        format!(
            r#"你是一位专业的瑜伽教练。请分析以下瑜伽动作：

动作名称：{}

## 关节角度数据
- 左肘角度: {:.1}°
- 右肘角度: {:.1}°
- 左膝角度: {:.1}°
- 右膝角度: {:.1}°
- 左髋角度: {:.1}°
- 右髋角度: {:.1}°
- 左肩角度: {:.1}°
- 右肩角度: {:.1}°
- 脊柱角度: {:.1}°
- 身体倾斜: {:.1}°

## 姿态图统计
- 节点数: {}
- 边数: {}
- 平均可见性: {:.2}
- 最大距离: {:.3}
- 平均距离: {:.3}

## 稳定性评分: {:.1}/10

请按照以下格式输出评估结果：

## 综合评分
总分: XX/100
- 结构准确性: XX/60
- 正位性: XX/30
- 稳定性: XX/10

## 主要问题
1. 问题1
2. 问题2

## 改进建议
1. 建议1
2. 建议2"#,
            pose_name,
            angle_data.left_elbow.unwrap_or(0.0),
            angle_data.right_elbow.unwrap_or(0.0),
            angle_data.left_knee.unwrap_or(0.0),
            angle_data.right_knee.unwrap_or(0.0),
            angle_data.left_hip.unwrap_or(0.0),
            angle_data.right_hip.unwrap_or(0.0),
            angle_data.left_shoulder.unwrap_or(0.0),
            angle_data.right_shoulder.unwrap_or(0.0),
            angle_data.spine_angle.unwrap_or(0.0),
            angle_data.body_tilt.unwrap_or(0.0),
            graph.stats.num_nodes,
            graph.stats.num_edges,
            graph.stats.avg_visibility,
            graph.stats.max_distance,
            graph.stats.avg_distance,
            stability_score,
        )
    }

    /// Parse assessment response
    fn parse_assessment_response(&self, response: &str, angle_data: &AngleData,
                                 graph: &PoseGraph, stability_score: f64) -> Result<AssessmentResult> {
        let mut total_score = 70.0;
        let mut structure_score = 45.0;
        let mut alignment_score = 20.0;
        let mut stability_score_out = stability_score * 1.0;
        let mut problems = Vec::new();
        let mut suggestions = Vec::new();

        // Simple parsing logic (in production, use more robust parsing)
        for line in response.lines() {
            let line = line.trim();

            if line.starts_with("总分:") {
                if let Some(score) = Self::extract_score(line) {
                    total_score = score;
                }
            } else if line.starts_with("结构准确性:") {
                if let Some(score) = Self::extract_score(line) {
                    structure_score = score;
                }
            } else if line.starts_with("正位性:") {
                if let Some(score) = Self::extract_score(line) {
                    alignment_score = score;
                }
            } else if line.starts_with("稳定性:") {
                if let Some(score) = Self::extract_score(line) {
                    stability_score_out = score;
                }
            } else if line.starts_with(|c: char| c.is_numeric()) && line.contains('.') {
                if problems.len() < 3 {
                    let problem = line.splitn(2, '.').nth(1).unwrap_or(line).trim();
                    if !problem.is_empty() && !problem.contains("稳定性") {
                        problems.push(problem.to_string());
                    }
                }
            } else if problems.len() >= suggestions.len() && !line.is_empty() && line.len() > 5 {
                let suggestion = line.splitn(2, '.').nth(1).unwrap_or(line).trim();
                if !suggestion.is_empty() && !suggestion.contains("建议") {
                    suggestions.push(suggestion.to_string());
                }
            }
        }

        // Add default suggestions if none found
        if suggestions.is_empty() {
            suggestions.push("保持动作稳定".to_string());
            suggestions.push("注意呼吸配合".to_string());
        }

        Ok(AssessmentResult {
            total_score,
            structure_score,
            alignment_score,
            stability_score: stability_score_out,
            problems,
            suggestions,
            angle_data: angle_data.clone(),
            graph_data: graph.clone(),
            model_response: response.to_string(),
        })
    }

    /// Extract score from text
    fn extract_score(text: &str) -> Option<f64> {
        let parts: Vec<&str> = text.split('/').collect();
        if parts.len() == 2 {
            parts[0].split_whitespace()
                .last()
                .and_then(|s| s.parse::<f64>().ok())
        } else {
            text.split_whitespace()
                .find_map(|s| s.parse::<f64>().ok())
        }
    }
}
