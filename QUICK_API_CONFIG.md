# 线上 API 快速配置指南

## 30 秒快速开始

### 1. 选择 API

| 推荐指数 | API | 配置 | 成本 |
|---------|-----|------|------|
| ⭐⭐⭐⭐⭐ | **OpenAI GPT-4o** | 最快最强 | $0.005/次 |
| ⭐⭐⭐⭐⭐ | **Claude 3 Sonnet** | 平衡好 | $0.003/次 |
| ⭐⭐⭐⭐ | **Gemini Flash** | 免费层 | 免费 |
| ⭐⭐⭐ | **本地 LLaVA** | 完全免费 | $0 |

### 2. 获取 API Key

**OpenAI:** https://platform.openai.com/api-keys
**Claude:** https://console.anthropic.com/keys
**Gemini:** https://aistudio.google.com/app/apikey

### 3. 配置 `config/settings.py`

复制粘贴相应的配置段落：

#### 选项 A: OpenAI GPT-4o ✅ 推荐

```python
MULTIMODAL_CONFIG = {
    "api_url": "https://api.openai.com/v1",
    "model": "gpt-4o",
    "api_type": "openai",
    "api_key": "sk-your-key-here",
    "timeout": 120,
    "temperature": 0.7,
}
```

#### 选项 B: Claude 3 Sonnet

```python
MULTIMODAL_CONFIG = {
    "api_url": "https://api.anthropic.com",
    "model": "claude-3-sonnet-20240229",
    "api_type": "claude",
    "api_key": "sk-ant-your-key-here",
    "timeout": 120,
    "temperature": 0.7,
}
```

#### 选项 C: Gemini Flash (免费)

```python
MULTIMODAL_CONFIG = {
    "api_url": "https://generativelanguage.googleapis.com",
    "model": "gemini-1.5-flash",
    "api_type": "gemini",
    "api_key": "AIzaSy_your_key_here",
    "timeout": 120,
    "temperature": 0.7,
}
```

#### 选项 D: 本地 LLaVA

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

### 4. 启动系统

```bash
# 终端 1: 启动后端
cd d:\yuga_test
python python_api.py

# 终端 2: 启动前端
cd d:\yuga_test\js_frontend
python -m http.server 3000

# 浏览器打开
# http://localhost:3000
```

### 5. 测试连接

```bash
python test_multimodal_api.py --test-connection
```

---

## 常见错误解决

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `401 Unauthorized` | API Key 无效 | 检查 Key 是否正确、是否过期 |
| `Connection timeout` | 网络问题 | 检查网络连接，增加 timeout |
| `Rate limit exceeded` | 请求过频繁 | 等待若干秒后重试 |
| `Model not found` | 模型名称错误 | 确认模型名是否正确 |

---

## 成本估算

每次评估视频（约 30 秒）:

| API | 费用 | 月用量 (100 次) |
|-----|------|-----------------|
| GPT-4o | $0.010 | $1 |
| Claude Sonnet | $0.003 | $0.30 |
| Gemini Flash | $0 | $0 (免费层) |
| 本地 LLaVA | $0 | $0 |

---

## 环境变量配置 (推荐生产方案)

不建议在代码中写 API Key，改用环境变量：

### Windows PowerShell

```powershell
$env:MULTIMODAL_API_KEY = "sk-..."
$env:MULTIMODAL_API_TYPE = "openai"
```

### Linux/Mac

```bash
export MULTIMODAL_API_KEY="sk-..."
export MULTIMODAL_API_TYPE="openai"
```

然后修改 `config/settings.py`:

```python
import os

MULTIMODAL_CONFIG = {
    "api_url": "https://api.openai.com/v1",
    "model": "gpt-4o",
    "api_type": os.getenv("MULTIMODAL_API_TYPE", "openai"),
    "api_key": os.getenv("MULTIMODAL_API_KEY"),
    "timeout": 120,
    "temperature": 0.7,
}
```

---

## 高级配置

### 使用代理

如果在国内或受限网络环境：

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

# 配置代理
proxies = {
    "https": "socks5://127.0.0.1:1080",  # Proxies
}
```

### 异步并发处理

```python
import asyncio

async def analyze_multiple_videos(videos):
    tasks = [
        analyze_video_async(video) 
        for video in videos
    ]
    return await asyncio.gather(*tasks)
```

---

## 支持情况

| 功能 | OpenAI | Claude | Gemini | LLaVA |
|------|--------|--------|--------|-------|
| 文本分析 | ✅ | ✅ | ✅ | ✅ |
| 图像分析 | ✅ | ✅ | ✅ | ✅ |
| 并发请求 | ✅ | ✅ | ✅ | ✅ |
| 成本低廉 | ✗ | ✓ | ✓✓ | ✓✓✓ |
| 离线运行 | ✗ | ✗ | ✗ | ✅ |

---

## 获取帮助

- 查看详细文档: `ONLINE_API_GUIDE.md`
- 查看日志输出: `python_api.py` 控制台
- 测试脚本: `python test_multimodal_api.py --help`

---

最后更新：2026-04-06
