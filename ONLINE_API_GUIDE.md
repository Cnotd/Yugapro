# 线上多模态 API 集成指南

## 概述

系统已升级为支持线上多模态 API，可以调用云端的 AI 模型进行视频分析，包括：

- **OpenAI Vision** (gpt-4-vision, gpt-4o)
- **Claude Vision** (最新的 Claude 3 系列)
- **Google Gemini** (Gemini 1.5 等)
- **本地 API** (LLaVA, Qwen 等)

## 快速开始

### 方案 1: 使用 OpenAI Vision（推荐）

#### 1.1 获取 API Key
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 创建新的 API Key
3. 复制 API Key

#### 1.2 配置系统
编辑 `config/settings.py`：

```python
MULTIMODAL_CONFIG = {
    "api_url": "https://api.openai.com/v1",
    "model": "gpt-4-vision",  # 或 gpt-4o
    "api_type": "openai",
    "api_key": "sk-your-key-here",
    "timeout": 120,
    "temperature": 0.7,
}
```

#### 1.3 启动系统
```bash
# 启动后端
python python_api.py

# 启动前端（另一个终端）
cd js_frontend
python -m http.server 3000

# 打开浏览器
# http://localhost:3000
```

**预期费用：**
- gpt-4-vision: 约 $0.01-0.03 / 请求
- gpt-4o: 约 $0.005-0.015 / 请求

---

### 方案 2: 使用 Claude Vision

#### 2.1 获取 API Key
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建 API Key
3. 复制密钥

#### 2.2 配置系统
编辑 `config/settings.py`：

```python
MULTIMODAL_CONFIG = {
    "api_url": "https://api.anthropic.com",
    "model": "claude-3-opus-20240229",  # 或 claude-3-sonnet
    "api_type": "claude",
    "api_key": "sk-ant-your-key-here",
    "timeout": 120,
    "temperature": 0.7,
}
```

**模型选择：**
- `claude-3-opus`: 最强，最贵
- `claude-3-sonnet`: 平衡性能和成本（推荐）
- `claude-3-haiku`: 速度快，便宜

**预期费用：**
- Opus: 约 $0.015-0.045 / 请求
- Sonnet: 约 $0.003-0.015 / 请求
- Haiku: 约 $0.0008-0.004 / 请求

---

### 方案 3: 使用 Google Gemini

#### 3.1 获取 API Key
1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 创建新的 API Key
3. 复制密钥

#### 3.2 配置系统
编辑 `config/settings.py`：

```python
MULTIMODAL_CONFIG = {
    "api_url": "https://generativelanguage.googleapis.com",
    "model": "gemini-1.5-pro",  # 或 gemini-1.5-flash
    "api_type": "gemini",
    "api_key": "AIzaSy_your_key_here",
    "timeout": 120,
    "temperature": 0.7,
}
```

**模型选择：**
- `gemini-1.5-pro`: 高精度
- `gemini-1.5-flash`: 速度快，成本低（推荐）

**预期费用：**
- 免费层: 每分钟 60 个请求
- Pro: $10/月

---

### 方案 4: 使用本地 LLaVA Vision

```python
MULTIMODAL_CONFIG = {
    "api_url": "http://localhost:8000",
    "model": "llava-1.5",
    "api_type": "llamavision",
    "api_key": None,
    "timeout": 120,
    "temperature": 0.7,
}
```

#### 启动本地 API
```bash
# 首先启动 LLaVA 服务器
python multimodal_server.py

# 然后启动后端
python python_api.py
```

---

## 成本对比

| API | 成本 | 速度 | 质量 |
|-----|------|------|------|
| OpenAI GPT-4V | 🔴 高 ($0.01) | ⚡⚡ 快 | ⭐⭐⭐⭐⭐ |
| OpenAI GPT-4o | 🟡 中 ($0.005) | ⚡⚡⚡ 很快 | ⭐⭐⭐⭐⭐ |
| Claude 3 Opus | 🔴 高 ($0.015) | ⚡ 中等 | ⭐⭐⭐⭐⭐ |
| Claude 3 Sonnet | 🟡 中 ($0.003) | ⚡⚡ 快 | ⭐⭐⭐⭐ |
| Gemini Pro | 🟢 低 (免费) | ⚡⚡ 快 | ⭐⭐⭐⭐ |
| LLaVA (本地) | 🟢 免费 | 🐌 慢 | ⭐⭐⭐ |

---

## API 提示词优化

系统会自动为每个 API 格式化瑜伽评估提示词。示例：

```
请分析这个瑜伽动作图像，基于以下信息给出评估：

姿态: Mountain Pose
检测质量: 37.5%（218/581 帧检测成功）

关键角度统计:
- Hip: 平均 175.2°（范围 170-180°）
- Knee: 平均 172.5°（范围 165-180°）
- Shoulder: 平均 177.8°（范围 170-180°）
- Spine: 平均 5.3°（范围 0-10°）

稳定性评分: 75/100

请提供:
1. 总体评分 (0-100)
2. 分项评分: 结构准确性, 对齐度, 稳定性
3. 识别的主要问题
4. 改进建议

返回 JSON 格式结果。
```

---

## 错误排查

### 连接失败
```
[MultimodalClient] 连接失败: 无法连接
```
**解决方案：**
- 检查网络连接
- 验证 API 密钥正确
- 确保 API 端点 URL 正确

### 认证失败
```
401 Unauthorized
```
**解决方案：**
- 检查 API Key 是否有效
- 检查 API Key 是否过期
- 检查 API 类型和 URL 是否匹配

### 请求超时
```
Timeout after 120 seconds
```
**解决方案：**
- 增加 `timeout` 值
- 检查网络速度
- 使用更快的 API（如 Gemini Flash）

### 配额限制
```
Rate limit exceeded
```
**解决方案：**
- 等待后重试
- 升级 API 套餐
- 使用本地 API

---

## 生产部署建议

### 安全性
1. **不要在代码中硬编码 API Key**
   ```python
   import os
   api_key = os.environ.get('MULTIMODAL_API_KEY')
   ```

2. **使用环境变量**
   ```bash
   export MULTIMODAL_API_KEY="sk-..."
   export MULTIMODAL_API_TYPE="openai"
   ```

3. **限制 API 访问**
   - 在云端设置 IP 白名单
   - 使用 API 配额限制

### 成本控制
1. **监控 API 使用量**
   - 在 OpenAI/Claude/Google 控制台设置警报
   - 使用 cost 标签分类请求

2. **优化请求**
   - 压缩图像到合理大小
   - 重用计算结果
   - 使用缓存

3. **选择合适的模型**
   - 对于简单任务，使用成本更低的模型
   - 对于复杂分析，使用更强的模型

### 性能优化
1. **并发请求**
   ```python
   # 当处理多个视频时使用异步
   asyncio.gather(
       analyze_video(video1),
       analyze_video(video2),
       analyze_video(video3)
   )
   ```

2. **请求队列**
   - 使用 Redis/RabbitMQ 管理队列
   - 实现指数退避重试

3. **缓存结果**
   - 缓存相似图像的结果
   - 减少重复请求

---

## 常见问题

**Q: 哪个 API 最划算？**
A: Google Gemini Flash（免费层）或 Claude 3 Haiku（$0.0008）

**Q: 支持批量处理吗？**
A: 是的，但需要自己实现异步处理逻辑

**Q: 可以离线使用吗？**
A: 可以，使用本地 LLaVA 服务器

**Q: 数据隐私如何保证？**
A: 使用本地模型；或选择支持数据加密的云服务

---

## 联系支持

有问题？
- 查看系统日志：`python_api.py` 的输出
- 检查 API 状态：https://status.openai.com (OpenAI)
- 查看错误消息中的详细信息

---

版本：1.1 | 更新时间：2026-04-06
