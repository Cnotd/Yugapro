# 环境配置说明

## 环境信息

- **环境名称**: yuga
- **Python 版本**: 3.9
- **Conda 路径**: D:\conda

## 快速启动

### 方法1：使用启动脚本（推荐）

双击运行 `start_yuga.bat`，环境会自动激活。

### 方法2：手动激活

在 PowerShell 中运行：
```bash
conda activate yuga
```

## 已安装的关键包

- **opencv-python**: 4.13.0.92
- **mediapipe**: 0.10.5 (已降级以兼容旧版 API)
- **numpy**: 2.0.2
- **matplotlib**: 3.9.4
- **gradio**: 4.44.1
- **protobuf**: 3.20.3

## 常用命令

### 运行测试脚本
```bash
# 测试 Ardhakati Chakrasana 动作
python temp_tests/test_ardhakati.py

# 批量处理视频
python temp_tests/test_mediapipe_batch.py

# 运行主程序
python run.py
```

### 环境管理
```bash
# 查看已安装的包
pip list

# 安装新包
pip install package_name

# 退出环境
conda deactivate
```

## 解决常见问题

### 问题1：ModuleNotFoundError: No module named 'cv2'

**原因**: 环境未激活或 opencv 未安装

**解决**:
```bash
conda activate yuga
pip install opencv-python
```

### 问题2：MediaPipe API 错误

**原因**: MediaPipe 版本不兼容

**解决**:
```bash
pip install mediapipe==0.10.5 --force-reinstall
```

### 问题3：编码问题（中文乱码）

**原因**: Windows 默认编码问题

**解决**: 脚本已添加 UTF-8 编码设置，无需额外处理

## 注意事项

1. **每次打开新终端都需要激活 yuga 环境**
2. **不要使用 base 环境**（缺少项目依赖）
3. **MediaPipe 版本固定为 0.10.5**（不要随意升级）
4. **protobuf 版本固定为 3.20.3**（兼容 MediaPipe）
