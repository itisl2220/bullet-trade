"""
BulletTrade GUI 模块入口

可以通过以下方式启动：
    python -m bullet_trade.gui
"""

import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main())
