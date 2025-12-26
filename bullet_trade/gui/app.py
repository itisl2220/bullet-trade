"""
BulletTrade GUI 应用程序入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .main_window import MainWindow
from .config_manager import ConfigManager
from .auth_manager import AuthManager
from .login_dialog import LoginDialog
from ..utils.env_loader import load_env


class BulletTradeApp:
    """BulletTrade GUI 应用程序"""

    def __init__(self):
        """初始化应用程序"""
        self.app = None
        self.window = None
        self.auth_manager = None
        self.login_dialog = None

    def run(self):
        """运行GUI应用程序"""
        # 加载环境变量（从.env文件）
        load_env()

        # 加载GUI配置并应用到环境变量（优先级高于.env文件）
        config_manager = ConfigManager()
        config_manager.apply_to_env()

        # 初始化认证管理器
        self.auth_manager = AuthManager()

        # 清除旧的会话信息，强制重新登录
        # 因为现在只支持后端认证，旧的本地会话无效
        self.auth_manager.logout()

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

        # 检查登录状态
        if not self.auth_manager.is_authenticated():
            # 显示登录对话框
            if not self._show_login_dialog():
                # 登录失败，退出应用
                return 0

        # 创建主窗口
        self.window = MainWindow(auth_manager=self.auth_manager)
        self.window.show()

        # 运行事件循环
        return self.app.exec()

    def _show_login_dialog(self) -> bool:
        """
        显示登录对话框

        Returns:
            登录是否成功
        """
        self.login_dialog = LoginDialog()
        self.login_dialog.set_auth_manager(self.auth_manager)

        # 连接登录成功信号
        self.login_dialog.login_success.connect(self._on_login_success)

        # 显示登录对话框
        result = self.login_dialog.exec()

        return result == LoginDialog.DialogCode.Accepted

    def _on_login_success(self, username: str):
        """登录成功处理"""
        print(f"用户 {username} 登录成功")
        # 可以在这里添加登录成功后的额外处理逻辑


def main():
    """GUI入口函数"""
    app = BulletTradeApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
