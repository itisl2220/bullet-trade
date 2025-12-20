#!/usr/bin/env python
"""
BulletTrade GUI 启动脚本

直接运行此脚本启动图形界面：
    python start_gui.py
"""

import sys
from pathlib import Path

# 确保可以导入 bullet_trade
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from bullet_trade.gui.app import main
    
    if __name__ == '__main__':
        sys.exit(main())
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("\n请确保已安装 BulletTrade 和 GUI 依赖：")
    print("  pip install bullet-trade[gui]")
    print("\n或者安装 PyQt6：")
    print("  pip install PyQt6>=6.4.0")
    sys.exit(1)
except Exception as e:
    print(f"❌ 启动GUI失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

