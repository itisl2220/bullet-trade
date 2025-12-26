"""
BulletTrade GUI 模块

提供图形化用户界面，支持回测、实盘、参数优化等功能
"""

from .main_window import MainWindow
from .app import BulletTradeApp
from .auth_manager import AuthManager
from .login_dialog import LoginDialog

__all__ = ["MainWindow", "BulletTradeApp", "AuthManager", "LoginDialog"]
