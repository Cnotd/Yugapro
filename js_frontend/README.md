# 瑜伽动作智能评估系统 - 部署指南

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (JavaScript)                         │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │   HTML/CSS  │  │     JS      │  │   Charts    │       │
│   └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端 (Rust + Axum)                       │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│   │  Pose API   │  │ Video API   │  │ Admin API   │         │
│   └─────────────┘  └─────────────┘  └─────────────┘         │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│   │ PoseAnalyzer│  │OllamaClient│  │ DB Manager  │         │
│   └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (SQLite)                           │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
yuga_test/
├── rust_backend/          # Rust后端项目
│   ├── Cargo.toml
│   ├── src/
│   │   ├── main.rs       # 主入口
│   │   ├── lib.rs        # 库入口
│   │   ├── api/          # API端点
│   │   │   ├── mod.rs
│   │   │   ├── health.rs
│   │   │   ├── assessment.rs
│   │   │   ├── video.rs
│   │   │   ├── pose.rs
│   │   │   └── admin.rs
│   │   ├── models/       # 数据模型
│   │   │   └── mod.rs
│   │   ├── services/     # 业务逻辑
│   │   │   ├── mod.rs
│   │   │   ├── pose_analyzer.rs
│   │   │   ├── ollama_client.rs
│   │   │   └── video_processor.rs
│   │   └── db/           # 数据库
│   │       └── mod.rs
│   └── uploads/          # 上传文件目录
│
├── js_frontend/          # JavaScript前端项目
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── api.js        # API客户端
│   │   └── app.js        # 应用逻辑
│   └── assets/
│
└── docs/                 # 文档
```

## 环境要求

### Rust后端

- Rust 1.70+
- SQLite
- FFmpeg (用于视频处理)
- Ollama (用于AI模型)

### 前端

- 现代浏览器 (Chrome, Firefox, Safari, Edge)
- 支持 ES6+

## 安装步骤

### 1. 安装Rust

```bash
# Windows
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 或者使用 winget
winget install Rust.Rust
```

### 2. 安装FFmpeg

```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 3. 安装Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows - 从 https://ollama.ai 下载安装
```

### 4. 下载AI模型

```bash
ollama pull qwen3.5:4b
```

### 5. 构建后端

```bash
cd rust_backend

# Release构建
cargo build --release

# 开发构建
cargo build
```

### 6. 运行后端

```bash
# Release模式
./target/release/yoga-assessment-server

# 或开发模式
cargo run
```

服务器将在 `http://localhost:8080` 启动。

### 7. 配置环境变量

```bash
# 设置Ollama地址 (默认: http://localhost:11434)
export OLLAMA_URL=http://localhost:11434

# 设置模型名称 (默认: qwen3.5:4b)
export OLLAMA_MODEL=qwen3.5:4b
```

### 8. 运行前端

由于前端是纯静态文件，可以使用任意HTTP服务器：

```bash
# 使用Python
cd js_frontend
python -m http.server 3000

# 使用Node.js
npx serve .

# 使用VS Code Live Server扩展
```

然后访问 `http://localhost:3000`

## API文档

### 健康检查

```
GET /api/health

Response:
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-04-02T10:00:00Z"
}
```

### 上传视频

```
POST /api/assessment/upload
Content-Type: multipart/form-data

Fields:
- video: 文件 (必填)
- pose_name: 字符串 (可选, 默认"下犬式")

Response:
{
  "video_id": 1,
  "assessment_id": 1,
  "status": "processing",
  "message": "Video uploaded successfully"
}
```

### 获取评估状态

```
GET /api/assessment/:id

Response:
{
  "assessment_id": 1,
  "status": "completed",  // or "processing"
  "progress": 100,
  "result": {
    "total_score": 85,
    "structure_score": 52,
    "alignment_score": 25,
    "stability_score": 8,
    "problems": [...],
    "suggestions": [...],
    "angle_data": {...},
    "graph_data": {...}
  }
}
```

### 获取动作标准

```
GET /api/pose/standards

Response:
[
  {
    "id": 1,
    "pose_name": "下犬式",
    "pose_name_en": "Downward Dog",
    "category": "倒立",
    "difficulty_level": "初级",
    "hip_min": 160,
    "hip_max": 175,
    ...
  },
  ...
]
```

### 获取系统统计

```
GET /api/admin/stats

Response:
{
  "total_users": 100,
  "total_assessments": 500,
  "today_assessments": 15,
  "average_score": 78.5,
  "pose_types": 5,
  "active_users": 25
}
```

## 数据库

数据库文件位置: `data/yoga_assessment.db`

### 主要表

1. **user** - 用户信息
2. **assessment_record** - 评估记录
3. **pose_standard** - 动作标准库
4. **video_data** - 视频数据
5. **user_progress** - 用户进步跟踪

## 性能优化

### Rust后端

1. **启用Release模式**: 使用 `cargo build --release`
2. **LTO优化**: Cargo.toml中已启用
3. **并行处理**: 使用Tokio异步运行时

### 前端

1. **静态资源缓存**: 配置适当的Cache-Control
2. **懒加载**: 图片和视频按需加载
3. **代码分割**: 大型JavaScript文件分割

## 常见问题

### Q1: 后端启动失败

**问题**: `Failed to bind to address`

**解决**:
- 检查端口8080是否被占用
- 使用 `lsof -i :8080` (macOS/Linux) 或 `netstat -ano | findstr :8080` (Windows)

### Q2: Ollama连接失败

**问题**: `Ollama is not available`

**解决**:
- 确保Ollama正在运行: `ollama serve`
- 检查OLLAMA_URL环境变量
- 验证模型已下载: `ollama list`

### Q3: 视频处理失败

**问题**: FFmpeg相关错误

**解决**:
- 确保FFmpeg已安装并可访问
- 检查视频文件格式和大小
- 查看服务器日志

### Q4: 前端无法连接后端

**问题**: CORS错误

**解决**:
- 确认后端和前端使用相同的协议(http/https)
- 检查浏览器控制台错误信息
- 确认后端CORS配置

## 部署生产环境

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name yoga-assessment.example.com;

    # 前端静态文件
    location / {
        root /var/www/yoga-assessment/frontend;
        index index.html;
    }

    # API代理
    location /api {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用Systemd服务

```ini
[Unit]
Description=Yoga Assessment API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/yoga-assessment
ExecStart=/opt/yoga-assessment/rust_backend/target/release/yoga-assessment-server
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker部署 (TODO)

未来的Docker支持将使部署更加简单。

## 开发指南

### 添加新的API端点

1. 在 `src/api/` 创建新的模块文件
2. 在 `src/api/mod.rs` 中导出
3. 在 `src/main.rs` 中添加路由

### 添加新的数据模型

1. 在 `src/models/mod.rs` 中定义结构体
2. 使用 `#[derive(Serialize, Deserialize)]` 实现序列化

### 添加新的服务

1. 在 `src/services/` 创建新的服务文件
2. 在 `src/services/mod.rs` 中导出
3. 在 `AppState` 中注册服务

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系开发团队。
