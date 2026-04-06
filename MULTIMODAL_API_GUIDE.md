# 多模态 API 集成

## 概述
系统已全面集成多模态 API 支持，支持 LLaVA、Qwen 等多模态模型进行视频分析。

## 架构

```
前端 (Port 3000)
    ↓
Python Flask 后端 (Port 5000)
    ↓
多模态 API (Port 8000) ← [可选，默认不可用]
    ↓
简化评估 (内置)
```

## 快速开始

### 方案 1：使用简化评估（推荐快速体验）
无需额外配置，系统默认使用内置的简化评估引擎。

```bash
# 启动前端
cd js_frontend
python -m http.server 3000

# 启动后端（另一个终端）
cd d:\yuga_test
python python_api.py

# 打开浏览器
# http://localhost:3000
```

**特点：**
- ✅ 即插即用，无需模型
- ✅ 快速评估
- ✅ 基于关键点和角度的标准评估

### 方案 2：部署本地多模态 API 服务器

#### 2.1 安装依赖
```bash
# 基础依赖
pip install fastapi uvicorn pillow numpy

# 如果要使用 LLaVA 模型（需要 GPU，推荐 8GB+ VRAM）
pip install transformers torch torchvision torchaudio
```

#### 2.2 启动多模态服务器
```bash
# 开发/演示模式（无需真实模型）
python multimodal_server.py

# 访问文档
# http://localhost:8000/docs
```

**开发模式特点：**
- 无需下载模型
- 立即启动
- 返回示例结果

#### 2.3 配置后端使用多模态 API
编辑 `config/settings.py`：

```python
MULTIMODAL_CONFIG = {
    "api_url": "http://localhost:8000",
    "model": "llava-1.5",
    "api_type": "llamavision",  # 或 'qwen', 'generic'
    "timeout": 120,
    "temperature": 0.7,
}
```

**支持的 API 类型：**
- `llamavision` - LLaVA Vision API
- `qwen` - Qwen 多模态 API
- `generic` - 通用多模态 API（自定义端点）

#### 2.4 启动系统
```bash
# 终端 1：启动多模态 API
python multimodal_server.py

# 终端 2：启动后端
python python_api.py

# 终端 3：启动前端
cd js_frontend
python -m http.server 3000

# 打开浏览器
# http://localhost:3000
```

## 工作流程

### 用户上传视频 →
### 后端处理：
1. ✅ 读取视频
2. ✅ 检测人体关键点（MediaPipe）
3. ✅ 计算关键角度
4. ✅ 发送关键帧到多模态 API
5. ✅ 解析 API 响应获得分数和建议
6. ✅ 返回详细评估结果

### 降级策略：
- 如果多模态 API 不可用 → 尝试 Ollama
- 如果 Ollama 不可用 → 使用简化评估
- 确保系统始终能工作

## API 规范

### 后端 API

**上传视频进行评估**
```bash
POST /api/assessment/upload
Content-Type: multipart/form-data

- video: 视频文件
- pose_name: 瑜伽姿态名称 (Mountain Pose, Tree Pose, Warrior II, Triangle Pose, Chair Pose)
```

**获取评估状态**
```bash
GET /api/assessment/{assessment_id}

返回:
{
    "id": 1,
    "status": "completed|processing|failed",
    "progress": 50,
    "result": {...}
}
```

**获取详细结果**
```bash
GET /api/assessment/{assessment_id}/result

返回:
{
    "total_score": 85.0,
    "structure_score": 50.0,
    "alignment_score": 25.0,
    "stability_score": 10.0,
    "problems": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}
```

### 多模态 API

**方案 1：LLaVA Vision 兼容**
```bash
POST /v1/chat/completions

{
    "model": "llava-1.5",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
            {"type": "text", "text": "分析这个瑜伽姿态..."}
        ]
    }],
    "temperature": 0.7
}
```

**方案 2：通用端点**
```bash
POST /analyze

{
    "image": base64_encoded_image,
    "prompt": "分析提示词",
    "temperature": 0.7
}
```

## 自定义多模态 API

如果要集成自己的多模态模型：

### 步骤 1：创建 API 包装
继承 `MultimodalClient` 或创建兼容实现：

```python
class CustomMultimodalClient:
    def analyze_image_with_prompt(self, image, prompt):
        # 实现自己的逻辑
        pass
```

### 步骤 2：在后端注册
修改 `python_api.py` 中的初始化部分

### 步骤 3：更新配置
```python
MULTIMODAL_CONFIG = {
    "api_url": "http://your-custom-api",
    "api_type": "custom",
}
```

## 常见问题

**Q: 多模态 API 不可用时会怎样？**
A: 系统会自动降级到简化评估，仍能提供评分和建议。

**Q: 支持哪些瑜伽姿态？**
A: Mountain Pose（山式）、Tree Pose（树式）、Warrior II（战士二式）、Triangle Pose（三角式）、Chair Pose（椅子式）

**Q: 评估需要多长时间？**
A: 简化评估：5-10 秒；多模态 API：30-60 秒（取决于模型）

**Q: 可以离线使用吗？**
A: 是的，如果只使用简化评估，整个系统完全离线。

## 技术栈

- **前端**：Vanilla JavaScript
- **后端**：Python Flask
- **视频处理**：OpenCV, MediaPipe
- **多模态模型**：LLaVA, Qwen（可选）
- **API 框架**：FastAPI（多模态服务器）

## 联系方式

如有问题或建议，欢迎反馈！

---
版本：0.1.0 | 最后更新：2026-04-06
