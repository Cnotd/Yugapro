"""
简化版启动脚本
"""

import os
os.environ['GRADIO_SERVER_NAME'] = 'localhost'
os.environ['GRADIO_SERVER_PORT'] = '7860'

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import YogaAssessmentApp

app = YogaAssessmentApp()
interface = app.create_interface()

print("启动瑜伽动作评估系统...")
print("访问地址: http://localhost:7860")

interface.launch(share=False)
