"""
BulletTrade 主窗口
"""

import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QStatusBar, QMenuBar, QMenu, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from .pages.backtest_page import BacktestPage
from .pages.live_page import LivePage
from .pages.optimize_page import OptimizePage
from .pages.report_page import ReportPage
from .pages.strategy_page import StrategyPage
from .theme import get_main_stylesheet
from ..__version__ import __version__


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"BulletTrade - 量化交易系统 v{__version__}")
        self.setMinimumSize(1200, 800)
        
        # 创建菜单栏（已隐藏）
        # self._create_menu_bar()
        self.menuBar().setVisible(False)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
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
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
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
        self.strategy_page = StrategyPage()
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
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet(get_main_stylesheet())
    
    def _open_strategy(self):
        """打开策略文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择策略文件",
            str(Path.home()),
            "Python文件 (*.py);;所有文件 (*)"
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
        QMessageBox.information(
            self,
            "设置",
            "设置功能开发中..."
        )
    
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
            """
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
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()

