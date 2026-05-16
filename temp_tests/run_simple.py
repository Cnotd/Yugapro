"""
简化版启动脚本
"""

import os
os.environ['GRADIO_SERVER_NAME'] = 'localhost'
os.environ['GRADIO_SERVER_PORT'] = '7860'

import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.app import YogaAssessmentApp

app = YogaAssessmentApp()
interface = app.create_interface()

print("启动瑜伽动作评估系统...")
print("访问地址: http://127.0.0.1:7860")

interface.launch(
    server_name="127.0.0.1",
    server_port=7860,
    share=False
)
