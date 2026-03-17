"""
启动脚本 - 无代理版本
用于启动瑜伽动作评估系统
"""

import sys
import os

# 禁用所有代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    from src.app import main
    main()
