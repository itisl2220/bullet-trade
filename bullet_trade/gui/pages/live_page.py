"""
实盘交易页面
"""

import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ..theme import get_button_danger_style, get_log_text_style, COLORS


class LiveWorker(QThread):
    """实盘工作线程"""
    
    output = pyqtSignal(str)
    finished = pyqtSignal(int)
    
    def __init__(self, strategy_file, broker_name, runtime_dir, log_dir):
        super().__init__()
        self.strategy_file = strategy_file
        self.broker_name = broker_name
        self.runtime_dir = runtime_dir
        self.log_dir = log_dir
        self._running = True
    
    def run(self):
        """运行实盘"""
        try:
            from bullet_trade.core.live_engine import LiveEngine
            
            # 设置环境变量
            if self.runtime_dir:
                os.environ['RUNTIME_DIR'] = self.runtime_dir
            if self.log_dir:
                os.environ['LOG_DIR'] = self.log_dir
            
            overrides = {}
            if self.runtime_dir:
                overrides['runtime_dir'] = self.runtime_dir
            
            engine = LiveEngine(
                strategy_file=self.strategy_file,
                broker_name=self.broker_name,
                live_config=overrides or None,
            )
            
            self.output.emit("启动实盘引擎...")
            exit_code = engine.run()
            self.finished.emit(exit_code)
        except Exception as e:
            self.output.emit(f"错误: {e}")
            import traceback
            self.output.emit(traceback.format_exc())
            self.finished.emit(1)
    
    def stop(self):
        """停止实盘"""
        self._running = False
        self.terminate()


class LivePage(QWidget):
    """实盘交易页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 警告提示
        warning_label = QLabel(
            "⚠️ 警告：实盘交易涉及真实资金，请确保策略已充分测试！"
        )
        warning_label.setStyleSheet(f"""
            color: {COLORS['error']};
            font-weight: 600;
            padding: 12px;
            background-color: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 6px;
        """)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # 参数配置组
        config_group = QGroupBox("实盘配置")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(12)  # 设置表单行间距
        config_layout.setVerticalSpacing(12)  # 设置垂直间距
        
        # 策略文件
        strategy_layout = QHBoxLayout()
        self.strategy_file_edit = QLineEdit()
        self.strategy_file_edit.setPlaceholderText("选择策略文件...")
        strategy_layout.addWidget(self.strategy_file_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_strategy_file)
        strategy_layout.addWidget(browse_btn)
        config_layout.addRow("策略文件:", strategy_layout)
        
        # 券商类型
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["qmt", "qmt-remote", "simulator"])
        config_layout.addRow("券商类型:", self.broker_combo)
        
        # 运行时目录
        runtime_layout = QHBoxLayout()
        self.runtime_dir_edit = QLineEdit()
        self.runtime_dir_edit.setPlaceholderText("默认: runtime/live")
        runtime_layout.addWidget(self.runtime_dir_edit)
        runtime_browse_btn = QPushButton("浏览...")
        runtime_browse_btn.clicked.connect(self._browse_runtime_dir)
        runtime_layout.addWidget(runtime_browse_btn)
        config_layout.addRow("运行时目录:", runtime_layout)
        
        # 日志目录
        log_layout = QHBoxLayout()
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setPlaceholderText("默认: logs/live")
        log_layout.addWidget(self.log_dir_edit)
        log_browse_btn = QPushButton("浏览...")
        log_browse_btn.clicked.connect(self._browse_log_dir)
        log_layout.addWidget(log_browse_btn)
        config_layout.addRow("日志目录:", log_layout)
        
        layout.addWidget(config_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("启动实盘")
        self.start_btn.setStyleSheet(get_button_danger_style())
        self.start_btn.clicked.connect(self._start_live)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_live)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("状态: 未启动")
        self.status_label.setStyleSheet(f"""
            font-weight: 600;
            padding: 8px;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(self.status_label)
        
        # 输出日志
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(get_log_text_style())
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
    
    def _browse_strategy_file(self):
        """浏览策略文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择策略文件", str(Path.home()), "Python文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            self.strategy_file_edit.setText(file_path)
    
    def _browse_runtime_dir(self):
        """浏览运行时目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择运行时目录", self.runtime_dir_edit.text() or "runtime/live"
        )
        if dir_path:
            self.runtime_dir_edit.setText(dir_path)
    
    def _browse_log_dir(self):
        """浏览日志目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择日志目录", self.log_dir_edit.text() or "logs/live"
        )
        if dir_path:
            self.log_dir_edit.setText(dir_path)
    
    def _start_live(self):
        """启动实盘"""
        # 确认对话框
        reply = QMessageBox.warning(
            self,
            "确认启动实盘",
            "您确定要启动实盘交易吗？\n\n"
            "实盘交易将使用真实资金进行交易，请确保：\n"
            "1. 策略已充分回测验证\n"
            "2. 已正确配置券商账户\n"
            "3. 已设置适当的风险控制\n\n"
            "继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 验证参数
        strategy_file = self.strategy_file_edit.text().strip()
        if not strategy_file or not Path(strategy_file).exists():
            QMessageBox.warning(self, "错误", "请选择有效的策略文件")
            return
        
        # 启动工作线程
        self.worker = LiveWorker(
            strategy_file=strategy_file,
            broker_name=self.broker_combo.currentText(),
            runtime_dir=self.runtime_dir_edit.text().strip() or None,
            log_dir=self.log_dir_edit.text().strip() or None,
        )
        
        self.worker.output.connect(self._append_log)
        self.worker.finished.connect(self._on_live_finished)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("状态: 运行中")
        self.status_label.setStyleSheet(f"""
            font-weight: 600;
            padding: 8px;
            color: {COLORS['success']};
        """)
        self.log_text.clear()
        
        self.worker.start()
    
    def _stop_live(self):
        """停止实盘"""
        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止实盘交易吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait()
                self._append_log("实盘已停止")
                self._on_live_finished(1)
    
    def _append_log(self, message):
        """追加日志"""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def _on_live_finished(self, exit_code):
        """实盘完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        self.status_label.setStyleSheet(f"""
            font-weight: 600;
            padding: 8px;
            color: {COLORS['text_secondary']};
        """)
    
    def is_running(self):
        """检查是否正在运行"""
        return self.worker is not None and self.worker.isRunning()
    
    def set_strategy_file(self, file_path: str):
        """设置策略文件（由主窗口调用）"""
        self.strategy_file_edit.setText(file_path)

