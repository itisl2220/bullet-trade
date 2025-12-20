"""
BulletTrade GUI 应用程序入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .main_window import MainWindow
from .config_manager import ConfigManager
from ..utils.env_loader import load_env


class BulletTradeApp:
    """BulletTrade GUI 应用程序"""

    def __init__(self):
        """初始化应用程序"""
        self.app = None
        self.window = None

    def run(self):
        """运行GUI应用程序"""
        # 加载环境变量（从.env文件）
        load_env()
        
        # 加载GUI配置并应用到环境变量（优先级高于.env文件）
        config_manager = ConfigManager()
        config_manager.apply_to_env()

        # 创建QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("BulletTrade")
        self.app.setOrganizationName("BulletTrade")

        # 设置高DPI支持（兼容不同PyQt6版本）
        try:
            # PyQt6 6.2+ 中这些属性可能已弃用或不存在
            if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
                self.app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        except (AttributeError, TypeError):
            # 属性不存在时忽略，PyQt6 6.2+ 默认已启用高DPI
            pass

        try:
            if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
                self.app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except (AttributeError, TypeError):
            # 属性不存在时忽略
            pass

        # 创建主窗口
        self.window = MainWindow()
        self.window.show()

        # 运行事件循环
        return self.app.exec()


def main():
    """GUI入口函数"""
    app = BulletTradeApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
