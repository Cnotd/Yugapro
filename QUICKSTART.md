# 快速开始指南

## 系统要求

- Python 3.9+
- Windows 10/11 或 Linux
- (推荐) NVIDIA GPU 6GB+ 显存

## 快速启动(5分钟)

### 第一步: 安装依赖

```bash
cd d:/yuga_test
pip install -r requirements.txt
```

如果遇到安装问题,尝试:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 第二步: (可选) 配置Ollama

如果想要使用AI评估功能:

1. 下载Ollama: https://ollama.ai/

2. 安装后,拉取模型:
```bash
ollama pull qwen:7b
```

3. 验证服务是否运行:
```bash
curl http://localhost:11434/api/tags
```

### 第三步: 运行系统测试

```bash
python test_system.py
```

这会检查所有模块是否正常工作。

### 第四步: 启动应用

```bash
python run.py
```

看到以下输出说明启动成功:
```
启动瑜伽动作评估系统...
访问地址: http://localhost:7860
```

### 第五步: 使用系统

1. 打开浏览器访问 http://localhost:7860

2. 点击"上传视频"按钮,选择一个瑜伽视频文件
   - 支持格式: mp4, avi, mov
   - 大小限制: 100MB
   - 时长限制: 2分钟

3. 从下拉菜单选择动作类型:
   - 下犬式
   - 树式
   - 战士一式
   - 三角式
   - 猫牛式

4. 点击"开始评估"按钮

5. 等待处理完成,查看结果:
   - 标注视频(带骨骼连线)
   - 评分分布图
   - 角度变化曲线
   - 详细评估报告

## 常见问题

### Q1: 安装依赖失败

**解决方案:**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 无法启动Ollama

**解决方案:**
- 确保Ollama已安装: https://ollama.ai/download
- Windows: 从开始菜单启动Ollama
- Linux/Mac: 运行 `ollama serve`

### Q3: 视频处理很慢

**可能原因:**
- 使用CPU而非GPU
- 视频分辨率过高
- 视频帧数过多

**解决方案:**
- 使用GPU加速(需要CUDA)
- 降低视频分辨率
- 减少视频时长

### Q4: 关键点检测失败

**可能原因:**
- 光线不足
- 人物不清晰
- 姿态被遮挡

**解决方案:**
- 在明亮环境下拍摄
- 确保人物清晰可见
- 避免姿态被遮挡

### Q5: Gradio界面无法访问

**解决方案:**
- 检查端口7860是否被占用
- 尝试其他端口:
```python
# 修改 run.py 或 src/app.py
interface.launch(server_port=7861)  # 改用7861端口
```

### Q6: 看不到中文图表

**解决方案:**
系统已配置中文字体,如果仍有问题:
```bash
pip install matplotlib
# 系统会自动使用系统字体
```

## 测试系统

运行测试脚本验证各模块:
```bash
# 测试视频读取模块
python tests/test_video_reader.py

# 测试角度计算模块
python tests/test_angle_calculator.py

# 测试Ollama客户端
python tests/test_ollama_client.py

# 运行完整系统测试
python test_system.py
```

## 获取帮助

如果遇到问题:
1. 查看 README.md 获取详细文档
2. 运行 test_system.py 检查系统状态
3. 检查控制台输出的错误信息

## 性能优化建议

1. **使用GPU加速**
   - 安装CUDA
   - 安装GPU版本的OpenCV和MediaPipe

2. **降低视频质量**
   - 分辨率: 建议720p或以下
   - 帧率: 30fps即可

3. **减少视频时长**
   - 建议15-30秒的视频
   - 聚焦核心动作

## 示例使用场景

### 场景1: 自我练习评估

1. 拍摄自己的瑜伽动作视频
2. 上传到系统
3. 查看AI评估和建议
4. 根据建议改进动作

### 场景2: 动作教学辅助

1. 准备标准动作视频
2. 上传评估验证准确性
3. 作为教学参考
4. 帮助学生理解动作要点

### 场景3: 进步追踪

1. 定期拍摄练习视频
2. 记录每次评估结果
3. 对比不同时间段的评分
4. 追踪进步轨迹

## 下一步

- 查看 README.md 了解更多细节
- 探索 config/settings.py 自定义动作标准
- 修改 src/app.py 定制界面
- 添加更多瑜伽动作到标准库

享受您的瑜伽之旅! 🧘‍♀️
