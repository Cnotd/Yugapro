"""
启动脚本
用于启动瑜伽动作评估系统
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    from src.app import main
    main()
