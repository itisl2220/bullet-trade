"""
BulletTrade 主窗口
"""

import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QStatusBar,
    QMenuBar,
    QMenu,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from .pages.backtest_page import BacktestPage
from .pages.config_page import ConfigPage
from .pages.live_page import LivePage
from .pages.optimize_page import OptimizePage
from .pages.report_page import ReportPage
from .pages.strategy_page import StrategyPage
from .auth_manager import AuthManager
from .theme import get_main_stylesheet
from ..__version__ import __version__


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, auth_manager: AuthManager = None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager or AuthManager()
        self.current_user = self.auth_manager.get_current_user()
        self.current_username = self.auth_manager.get_current_username()

        self.setWindowTitle(f"BulletTrade - 量化交易系统 v{__version__}")
        self.setMinimumSize(1200, 800)

        # 创建状态栏
        self._setup_status_bar()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        main_layout.addWidget(self.tabs)

        # 添加各个页面
        self._create_pages()

        # 设置样式
        self._apply_styles()

    def _setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()

        # 显示欢迎信息
        if self.current_username:
            welcome_msg = f"欢迎使用 BulletTrade，用户: {self.current_username}"
        else:
            welcome_msg = "欢迎使用 BulletTrade"

        status_bar.showMessage(welcome_msg)

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 用户菜单
        if self.current_username:
            user_menu = menubar.addMenu(f"用户: {self.current_username}(&U)")

            user_info_action = QAction("用户信息(&I)", self)
            user_info_action.triggered.connect(self._show_user_info)
            user_menu.addAction(user_info_action)

            user_menu.addSeparator()

            logout_action = QAction("登出(&L)", self)
            logout_action.triggered.connect(self._logout)
            user_menu.addAction(logout_action)

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        open_strategy_action = QAction("打开策略(&O)", self)
        open_strategy_action.setShortcut("Ctrl+O")
        open_strategy_action.triggered.connect(self._open_strategy)
        file_menu.addAction(open_strategy_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        settings_action = QAction("设置(&S)", self)
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_pages(self):
        """创建各个功能页面"""
        # 策略管理页面
        self.strategy_page = StrategyPage(self.auth_manager)
        self.tabs.addTab(self.strategy_page, "策略管理")

        # 回测页面
        self.backtest_page = BacktestPage()
        self.tabs.addTab(self.backtest_page, "回测")

        # 实盘页面
        self.live_page = LivePage()
        self.tabs.addTab(self.live_page, "实盘交易")

        # 参数优化页面
        self.optimize_page = OptimizePage()
        self.tabs.addTab(self.optimize_page, "参数优化")

        # 报告页面
        self.report_page = ReportPage()
        self.tabs.addTab(self.report_page, "报告")

        # 配置页面
        self.config_page = ConfigPage()
        self.tabs.addTab(self.config_page, "配置")

    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet(get_main_stylesheet())

    def _open_strategy(self):
        """打开策略文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择策略文件", str(Path.home()), "Python文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            # 通知所有页面加载文件
            self.strategy_page.load_strategy_file(file_path)
            self.backtest_page.set_strategy_file(file_path)
            self.live_page.set_strategy_file(file_path)
            self.optimize_page.set_strategy_file(file_path)
            self.tabs.setCurrentWidget(self.strategy_page)
            self.statusBar().showMessage(f"已加载策略: {file_path}", 3000)

    def _show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能开发中...")

    def _show_user_info(self):
        """显示用户信息"""
        user_info = self.auth_manager.get_user_info()
        if user_info:
            QMessageBox.information(
                self,
                "用户信息",
                f"""
                <h3>用户详情</h3>
                <p><b>用户名:</b> {user_info.get('username', '未知')}</p>
                <p><b>角色:</b> {user_info.get('role_name', '未知')}</p>
                <p><b>邮箱:</b> {user_info.get('email', '未设置')}</p>
                <p><b>超级管理员:</b> {'是' if user_info.get('is_super_admin', False) else '否'}</p>
                """,
            )
        else:
            QMessageBox.warning(self, "错误", "无法获取用户信息")

    def _logout(self):
        """用户登出"""
        reply = QMessageBox.question(
            self,
            "确认登出",
            "确定要登出当前用户吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.auth_manager.logout()
            QMessageBox.information(self, "登出成功", "您已成功登出系统")
            self.close()

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 BulletTrade",
            f"""
            <h2>BulletTrade</h2>
            <p>专业的量化交易系统</p>
            <p>版本: {__version__}</p>
            <p>兼容聚宽API，支持多数据源和实盘交易</p>
            <p><a href="https://github.com/BulletTrade/bullet-trade">GitHub</a></p>
            """,
        )

    def closeEvent(self, event):
        """关闭事件处理"""
        # 检查是否有正在运行的任务
        if self.live_page.is_running():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "实盘交易正在运行，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()
