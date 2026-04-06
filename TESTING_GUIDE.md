# 瑜伽姿态智能评估系统 - 测试指南

## 📋 测试概述

本文档描述了如何测试瑜伽姿态智能评估系统的各个组件。

### 测试环境要求

- Python 3.9+
- Rust 1.70+
- 16GB RAM
- Windows 10/11 或 Linux/macOS

---

## 🚀 快速开始测试

### 1. 环境检查

运行环境检查脚本：

```bash
python test_system.bat
```

这将检查：
- ✅ Python环境
- ✅ Rust环境
- ✅ Cargo依赖
- ✅ 前端文件完整性
- ✅ 后端文件完整性
- ✅ Rust编译测试

### 2. 启动后端服务

#### Windows

```bash
cd rust_backend
cargo build --release
.\target\release\yoga-assessment-server
```

#### Linux/macOS

```bash
cd rust_backend
cargo build --release
./target/release/yoga-assessment-server
```

后端服务将在 `http://localhost:8080` 启动。

### 3. 启动前端服务

```bash
cd js_frontend
python -m http.server 3000
```

前端将在 `http://localhost:3000` 启动。

---

## 🧪 功能测试

### 1. 健康检查测试

```bash
curl http://localhost:8080/api/health
```

**预期响应：**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "connected",
  "pose_analyzer": "ready"
}
```

### 2. 获取动作标准列表

```bash
curl http://localhost:8080/api/pose/standards
```

**预期响应：**
```json
{
  "standards": [
    {
      "id": 1,
      "name": "Ardhakati Chakrasana",
      "display_name": "半月式",
      "hip_range": [150, 175],
      "knee_range": [165, 180],
      "shoulder_range": [160, 180],
      "spine_range": [0, 15]
    }
  ]
}
```

### 3. 上传视频测试

```bash
curl -X POST http://localhost:8080/api/assessment/upload \
  -F "video=@test_video.mp4" \
  -F "pose_name=Mountain Pose"
```

**预期响应：**
```json
{
  "id": "uuid-string",
  "status": "processing",
  "message": "Video uploaded successfully, processing started"
}
```

### 4. 获取评估结果

```bash
curl http://localhost:8080/api/assessment/{id}
```

**预期响应：**
```json
{
  "id": "uuid-string",
  "status": "completed",
  "total_score": 85.5,
  "structure_score": 52,
  "alignment_score": 26,
  "stability_score": 7.5,
  "problems": [
    "右膝角度略小，可能存在过度伸展",
    "髋部略微向左倾斜"
  ],
  "suggestions": [
    "建议加深右膝弯曲角度",
    "注意保持髋部水平"
  ],
  "created_at": "2026-04-02T10:30:00Z"
}
```

### 5. 获取系统统计

```bash
curl http://localhost:8080/api/admin/stats
```

**预期响应：**
```json
{
  "total_assessments": 150,
  "total_users": 25,
  "avg_score": 78.5,
  "today_assessments": 5,
  "pose_distribution": {
    "Mountain Pose": 45,
    "Tree Pose": 30,
    "Warrior II": 25,
    "Triangle Pose": 20,
    "Chair Pose": 30
  }
}
```

---

## 🎨 前端功能测试

### 测试清单

- [ ] 首页加载，显示系统统计
- [ ] 导航菜单切换流畅
- [ ] 视频上传功能正常
  - [ ] 支持拖拽上传
  - [ ] 支持点击选择
  - [ ] 显示上传预览
  - [ ] 支持格式验证
  - [ ] 支持大小限制检查
- [ ] 动作选择正常
  - [ ] 显示动作列表
  - [ ] 支持多选
  - [ ] 显示选中状态
- [ ] 评估按钮状态正确
  - [ ] 未选择视频时禁用
  - [ ] 选择视频后启用
- [ ] 评估结果显示正确
  - [ ] 显示总分
  - [ ] 显示分数分解
  - [ ] 显示角度图表
  - [ ] 显示问题列表
  - [ ] 显示改进建议
- [ ] 历史记录功能正常
  - [ ] 显示评估历史
  - [ ] 支持翻页
  - [ ] 支持详情查看
- [ ] 加载动画显示正确
- [ ] 错误提示正常

---

## 🔧 单元测试

### Rust后端单元测试

```bash
cd rust_backend
cargo test
```

### Python版本单元测试

```bash
cd src
python -m pytest tests/ -v
```

---

## 📊 性能测试

### 视频处理速度测试

```bash
# 测试单个视频处理时间
time curl -X POST http://localhost:8080/api/assessment/upload \
  -F "video=@test_video.mp4"
```

**性能指标：**
- 目标：≤30秒/分钟视频
- 实测应接近：18秒/分钟视频

### 并发测试

```bash
# 同时发送10个请求
for i in {1..10}; do
  curl -X POST http://localhost:8080/api/assessment/upload \
    -F "video=@test_video.mp4" &
done
wait
```

### 内存占用测试

```bash
# Linux/macOS
ps aux | grep yoga-assessment-server

# Windows
tasklist | findstr yoga-assessment-server
```

**目标：≤200MB（Rust版本）**

---

## 🐛 常见问题排查

### 1. 后端启动失败

**问题：** `Database connection failed`

**解决方案：**
```bash
# 确保data目录存在
mkdir -p data

# 初始化数据库
cd rust_backend
cargo run --bin init_db
```

### 2. 前端无法连接后端

**问题：** `Failed to fetch`

**解决方案：**
```bash
# 检查后端是否运行
curl http://localhost:8080/api/health

# 检查CORS配置
# 确保后端允许跨域请求
```

### 3. 视频上传失败

**问题：** `File too large` 或 `Invalid format`

**解决方案：**
```bash
# 检查文件大小（应<100MB）
ls -lh test_video.mp4

# 检查文件格式（应为mp4/avi/mov）
file test_video.mp4
```

### 4. 编译错误

**问题：** `cargo build` 失败

**解决方案：**
```bash
# 更新依赖
cargo update

# 清理并重新编译
cargo clean
cargo build --release
```

---

## ✅ 测试验收标准

| 测试项 | 验收标准 | 状态 |
|--------|---------|------|
| 后端编译 | 无错误 | ✅ |
| 后端启动 | 正常启动，无崩溃 | ⏳ |
| 健康检查 | 返回200状态码 | ⏳ |
| 视频上传 | 成功上传，返回UUID | ⏳ |
| 评估处理 | 正确计算分数 | ⏳ |
| 前端加载 | 无JavaScript错误 | ⏳ |
| 页面导航 | 切换流畅 | ⏳ |
| 视频上传UI | 功能正常 | ⏳ |
| 结果展示 | 显示完整 | ⏳ |
| 错误处理 | 提示友好 | ⏳ |

---

## 📞 测试报告模板

```markdown
## 测试报告

### 测试人员：___
### 测试日期：___

### 测试环境
- 操作系统：___
- Python版本：___
- Rust版本：___

### 测试结果

| 功能 | 测试结果 | 问题 |
|------|---------|------|
|      |         |      |

### 问题列表

1. 
2. 

### 改进建议

1. 
2. 

### 总体评价

- 优点：
- 缺点：
- 建议：
```

---

## 🎯 下一步

测试通过后，可以：

1. **提交代码到GitHub**
2. **部署到生产环境**
3. **集成CI/CD流程**
4. **添加更多动作标准**
5. **优化性能**

---

**测试愉快！🧘‍♂️**
