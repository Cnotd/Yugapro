"""
Flask Web界面
替代Gradio的备用方案
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, send_file
import tempfile
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.video_reader import VideoReader
from src.pose_detector import PoseDetector
from src.angle_calculator import AngleCalculator
from src.stats_calculator import StatsCalculator
from src.prompt_builder import PromptBuilder
from src.ollama_client import OllamaClient
from src.result_parser import ResultParser
from src.simple_evaluator import SimpleEvaluator
from config.settings import POSE_STANDARDS

app = Flask(__name__)

# 初始化各模块
video_reader = VideoReader()
pose_detector = PoseDetector()
angle_calculator = AngleCalculator()
stats_calculator = StatsCalculator()
prompt_builder = PromptBuilder()
ollama_client = OllamaClient()
result_parser = ResultParser()
simple_evaluator = SimpleEvaluator()

# 检查Ollama连接
ollama_available = ollama_client.check_connection()

# 创建临时目录
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/')
def index():
    """主页"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>瑜伽动作评估系统</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #34495e;
            }
            input[type="file"], select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }
            button {
                background-color: #3498db;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
            }
            button:hover {
                background-color: #2980b9;
            }
            #result {
                margin-top: 20px;
                padding: 20px;
                background-color: #ecf0f1;
                border-radius: 5px;
                display: none;
            }
            .score-display {
                font-size: 24px;
                font-weight: bold;
                color: #2ecc71;
                margin-bottom: 20px;
            }
            .info-box {
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 10px;
                margin-bottom: 15px;
            }
            .loading {
                text-align: center;
                padding: 20px;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧘 瑜伽动作评估系统</h1>
            
            <div class="info-box">
                <strong>支持的瑜伽动作：</strong>
                下犬式、树式、战士一式、三角式、猫牛式
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="video">上传视频 (mp4, avi, mov, 最大100MB, 时长≤2分钟):</label>
                    <input type="file" id="video" name="video" accept=".mp4,.avi,.mov" required>
                </div>
                
                <div class="form-group">
                    <label for="pose">选择动作类型:</label>
                    <select id="pose" name="pose">
                        <option value="下犬式">下犬式</option>
                        <option value="树式">树式</option>
                        <option value="战士一式">战士一式</option>
                        <option value="三角式">三角式</option>
                        <option value="猫牛式">猫牛式</option>
                    </select>
                </div>
                
                <button type="submit">开始评估</button>
            </form>
            
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>正在分析视频，请稍候...</p>
            </div>
            
            <div id="result">
                <div class="score-display" id="score"></div>
                <div id="details"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                var formData = new FormData(this);
                var loading = document.getElementById('loading');
                var result = document.getElementById('result');
                
                loading.style.display = 'block';
                result.style.display = 'none';
                
                fetch('/assess', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    loading.style.display = 'none';
                    
                    if (data.error) {
                        alert('错误: ' + data.error);
                        return;
                    }
                    
                    result.style.display = 'block';
                    
                    document.getElementById('score').innerHTML = 
                        '总分: ' + data.score + '/100';
                    
                    var details = `
                        <h3>详细评分</h3>
                        <ul>
                            <li>角度准确性: ${data.accuracy}/40</li>
                            <li>动作稳定性: ${data.stability}/30</li>
                            <li>整体协调性: ${data.coordination}/30</li>
                        </ul>
                        
                        <h3>主要问题</h3>
                        <ul>
                            ${data.problems.map(p => '<li>' + p + '</li>').join('')}
                        </ul>
                        
                        <h3>改进建议</h3>
                        <ul>
                            ${data.suggestions.map(s => '<li>' + s + '</li>').join('')}
                        </ul>
                        
                        ${data.annotated_video ? '<p><a href="/video/' + data.annotated_video + '" download>下载标注视频</a></p>' : ''}
                    `;
                    
                    document.getElementById('details').innerHTML = details;
                })
                .catch(error => {
                    loading.style.display = 'none';
                    alert('发生错误: ' + error);
                });
            });
        </script>
    </body>
    </html>
    '''


@app.route('/assess', methods=['POST'])
def assess():
    """评估视频"""
    try:
        # 获取上传的文件
        video_file = request.files['video']
        pose_name = request.form['pose']
        
        if not video_file:
            return jsonify({'error': '未上传视频文件'}), 400
        
        # 保存上传的视频
        video_path = TEMP_DIR / video_file.filename
        video_file.save(str(video_path))
        
        # 读取视频
        video_info, frames = video_reader.read(str(video_path))
        
        # 关键点检测
        landmarks_seq = pose_detector.detect_sequence(frames)
        
        # 过滤无效帧
        valid_landmarks = [lm for lm in landmarks_seq if lm is not None]
        if not valid_landmarks:
            return jsonify({'error': '未检测到有效的人体关键点'}), 400
        
        # 角度计算
        angles_seq = angle_calculator.compute_all(landmarks_seq)
        
        # 统计分析
        stats = stats_calculator.compute(angles_seq)
        stability_score = stats_calculator.compute_stability(landmarks_seq)
        
        # 构建提示词
        pose_standard = POSE_STANDARDS.get(pose_name)
        prompt = prompt_builder.build(stats, stability_score, pose_name, pose_standard)
        
        # 调用大模型评估
        if ollama_available:
            try:
                middle_idx = len(frames) // 2
                key_frame = frames[middle_idx]
                print(f"调用Ollama模型评估...")
                model_response = ollama_client.generate(prompt, key_frame)
                print(f"模型返回内容长度: {len(model_response)} 字符")
                assessment_result = result_parser.parse(model_response)
                
                if not assessment_result.get('success', False):
                    print(f"模型解析失败,使用简化评估")
                    print(f"解析错误: {assessment_result.get('error', 'Unknown')}")
                    print(f"原始响应前200字: {model_response[:200]}")
                    assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
                else:
                    print(f"模型评估成功")
            except Exception as e:
                print(f"Ollama调用失败: {str(e)}")
                print("使用简化评估模式")
                assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
        else:
            print("Ollama不可用,使用简化评估模式")
            assessment_result = simple_evaluator.evaluate(stats, stability_score, pose_name, pose_standard)
        
        # 绘制骨骼标注视频
        import cv2
        annotated_frames = []
        for i, (frame, landmarks) in enumerate(zip(frames, landmarks_seq)):
            if landmarks:
                annotated = pose_detector.draw_landmarks(frame, landmarks)
            else:
                annotated = frame
            annotated_frames.append(annotated)
        
        # 保存标注视频
        video_name = video_path.stem
        annotated_video_path = TEMP_DIR / f"{video_name}_annotated.mp4"
        
        height, width = frames[0].shape[:2]
        fps = video_info.get("fps", 30)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(annotated_video_path), fourcc, fps, (width, height))
        
        for frame in annotated_frames:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        out.release()
        
        # 返回结果
        result_data = assessment_result['data']['score']
        return jsonify({
            'score': result_data['total'],
            'accuracy': result_data['accuracy'],
            'stability': result_data['stability'],
            'coordination': result_data['coordination'],
            'problems': assessment_result['data']['problems'],
            'suggestions': assessment_result['data']['suggestions'],
            'annotated_video': annotated_video_path.name
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/video/<filename>')
def get_video(filename):
    """获取视频文件"""
    return send_file(str(TEMP_DIR / filename))


def _create_fallback_result(stats, stability_score):
    """创建备用评估结果(使用简化评估器)"""
    pose_standard = POSE_STANDARDS.get("下犬式", {})
    return simple_evaluator.evaluate(stats, stability_score, "下犬式", pose_standard)


if __name__ == '__main__':
    print("启动瑜伽动作评估系统...")
    print("访问地址: http://localhost:5000")
    print("\n注意: Flask版本功能较简化,如需完整功能请先解决Gradio问题")
    app.run(host='localhost', port=5000, debug=True)
