"""
实盘交易页面
"""

import os
import logging
import re
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
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ..theme import get_button_danger_style, get_log_text_style, COLORS
from ..config_manager import ConfigManager


class GuiLogHandler(logging.Handler):
    """将日志消息发送到GUI的信号处理器"""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        # 设置格式器，移除ANSI颜色代码
        self.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )

    def emit(self, record):
        """发送日志记录到GUI"""
        try:
            msg = self.format(record)
            # 移除ANSI颜色代码（GUI不需要）
            msg = re.sub(r"\033\[[0-9;]*m", "", msg)
            self.signal.emit(msg)
        except Exception:
            pass  # 忽略错误，避免影响实盘运行


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
        gui_handler = None
        try:
            from bullet_trade.core.live_engine import LiveEngine
            from bullet_trade.gui.config_manager import ConfigManager

            # 添加GUI日志处理器，将日志重定向到GUI
            from bullet_trade.core.globals import log

            gui_handler = GuiLogHandler(self.output)
            gui_handler.setLevel(logging.INFO)
            
            # 只添加到 log.logger，_sync_standard_logger() 会自动同步到 bullet_trade logger
            # 检查是否已存在相同的 handler，避免重复添加
            handler_exists = any(
                isinstance(h, GuiLogHandler) and h.signal == gui_handler.signal
                for h in log.logger.handlers
            )
            if not handler_exists:
                # 设置 log.logger 不传播，避免日志被 root logger 再次处理导致重复
                log.logger.propagate = False
                log.logger.addHandler(gui_handler)
                # 同步到 bullet_trade logger
                log._sync_standard_logger()

            # 应用GUI配置到环境变量（在子线程中也需要应用）
            config_manager = ConfigManager()
            config_manager.apply_to_env()

            # 设置环境变量
            if self.runtime_dir:
                os.environ["RUNTIME_DIR"] = self.runtime_dir
            if self.log_dir:
                os.environ["LOG_DIR"] = self.log_dir

            overrides = {}
            if self.runtime_dir:
                overrides["runtime_dir"] = self.runtime_dir

            engine = LiveEngine(
                strategy_file=self.strategy_file,
                broker_name=self.broker_name,
                live_config=overrides or None,
            )

            self.output.emit("启动实盘引擎...")
            exit_code = engine.run()
            self.finished.emit(exit_code)
        except Exception as e:
            error_msg = str(e)
            self.output.emit(f"错误: {error_msg}")

            # 提供更友好的QMT连接错误提示
            if (
                "xtquant" in error_msg.lower()
                or "qmt" in error_msg.lower()
                or "返回码: -1" in error_msg
            ):
                self.output.emit("")
                self.output.emit("=" * 60)
                self.output.emit("QMT连接失败排查建议：")
                self.output.emit("1. 确认QMT客户端已启动并登录")
                self.output.emit("2. 检查QMT账户ID是否正确（在QMT客户端中查看）")
                self.output.emit("3. 确认QMT数据路径配置正确")
                self.output.emit("4. 检查QMT客户端版本是否支持xtquant")
                self.output.emit("5. 尝试重启QMT客户端后重试")
                self.output.emit("")
                self.output.emit("💡 提示：如果QMT连接有问题，可以切换到模拟模式进行测试：")
                self.output.emit('   在实盘页面将"券商类型"改为"simulator"即可')
                self.output.emit("=" * 60)

            import traceback

            self.output.emit(traceback.format_exc())
            self.finished.emit(1)
        finally:
            # 清理日志处理器
            if gui_handler:
                try:
                    from bullet_trade.core.globals import log
                    # 从 log.logger 移除
                    if gui_handler in log.logger.handlers:
                        log.logger.removeHandler(gui_handler)
                    # 从 bullet_trade logger 移除（可能通过同步添加的）
                    bullet_trade_logger = logging.getLogger("bullet_trade")
                    if gui_handler in bullet_trade_logger.handlers:
                        bullet_trade_logger.removeHandler(gui_handler)
                    # 重新同步，确保 bullet_trade logger 的 handler 与 log.logger 一致
                    log._sync_standard_logger()
                except Exception:
                    pass  # 忽略清理错误

    def stop(self):
        """停止实盘"""
        self._running = False
        self.terminate()


class LivePage(QWidget):
    """实盘交易页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.config_manager = ConfigManager()
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        # 主布局：左右分栏
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧区域：配置和控制（占1/3）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 警告提示（动态显示）
        self.warning_label = QLabel("⚠️ 提示：当前使用模拟券商，不会使用真实资金。")
        self.warning_label.setStyleSheet(
            f"""
            color: {COLORS['info']};
            font-weight: 600;
            padding: 12px;
            background-color: #EFF6FF;
            border: 1px solid #93C5FD;
            border-radius: 6px;
        """
        )
        self.warning_label.setWordWrap(True)
        left_layout.addWidget(self.warning_label)

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

        # 券商类型（默认使用模拟模式）
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["simulator", "qmt", "qmt-remote"])
        # 根据配置设置默认值，确保默认是simulator
        default_broker = self.config_manager.get("broker", "simulator")
        # 如果配置中没有或配置错误，强制使用simulator
        if default_broker not in ["simulator", "qmt", "qmt-remote"]:
            default_broker = "simulator"
        index = self.broker_combo.findText(default_broker)
        if index >= 0:
            self.broker_combo.setCurrentIndex(index)
        else:
            # 如果找不到，默认选择simulator（索引0）
            self.broker_combo.setCurrentIndex(0)
        config_layout.addRow("券商类型:", self.broker_combo)
        
        # 券商类型变化时更新提示
        self.broker_combo.currentTextChanged.connect(self._on_broker_changed)
        # 初始化时调用一次，确保警告标签正确显示
        self._on_broker_changed(self.broker_combo.currentText())

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

        left_layout.addWidget(config_group)

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
        left_layout.addLayout(button_layout)

        # 状态标签
        self.status_label = QLabel("状态: 未启动")
        self.status_label.setStyleSheet(
            f"""
            font-weight: 600;
            padding: 8px;
            color: {COLORS['text_secondary']};
        """
        )
        left_layout.addWidget(self.status_label)

        left_layout.addStretch()  # 添加弹性空间，使内容靠上

        # 右侧区域：日志（占2/3）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 输出日志
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(get_log_text_style())
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_group)

        # 添加到主布局，设置拉伸比例：左侧1，右侧2
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 2)

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
    
    def _on_broker_changed(self, broker_name: str):
        """券商类型变化时的处理"""
        if broker_name == "simulator":
            self.warning_label.setText("⚠️ 提示：当前使用模拟券商，不会使用真实资金。")
            self.warning_label.setStyleSheet(
                f"""
                color: {COLORS['info']};
                font-weight: 600;
                padding: 12px;
                background-color: #EFF6FF;
                border: 1px solid #93C5FD;
                border-radius: 6px;
            """
            )
        else:
            self.warning_label.setText("⚠️ 警告：实盘交易涉及真实资金，请确保策略已充分测试！")
            self.warning_label.setStyleSheet(
                f"""
                color: {COLORS['error']};
                font-weight: 600;
                padding: 12px;
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                border-radius: 6px;
            """
            )

    def _start_live(self):
        """启动实盘"""
        # 应用GUI配置到环境变量（先应用，以便检查配置）
        self.config_manager.apply_to_env()

        # 检查配置（根据券商类型）
        broker_name = self.broker_combo.currentText()
        
        if broker_name == "simulator":
            # 模拟券商：只需要初始资金配置（可选）
            simulator_cash = self.config_manager.get("simulator_initial_cash", 1000000)
            if not simulator_cash or simulator_cash <= 0:
                QMessageBox.warning(
                    self,
                    "配置提示",
                    "模拟券商建议配置初始资金。\n\n"
                    '可在"配置"页面中设置"模拟器初始资金"（默认100万）。',
                )
        elif broker_name in ("qmt", "qmt-remote"):
            # QMT券商：需要QMT配置
            qmt_account_id = self.config_manager.get("qmt_account_id")
            qmt_data_path = self.config_manager.get("qmt_data_path")

            if broker_name == "qmt":
                if not qmt_account_id:
                    QMessageBox.warning(
                        self,
                        "配置错误",
                        "使用QMT券商需要配置QMT账户ID！\n\n" '请在"配置"页面中设置"QMT账户ID"。',
                    )
                    return

                if not qmt_data_path:
                    QMessageBox.warning(
                        self,
                        "配置错误",
                        "使用QMT券商需要配置QMT数据路径！\n\n"
                        '请在"配置"页面中设置"QMT数据路径"。\n'
                        "通常路径为：C:\\国金QMT交易端模拟\\userdata_mini",
                    )
                    return

                # 检查数据路径是否存在
                if qmt_data_path and not Path(qmt_data_path).exists():
                    reply = QMessageBox.warning(
                        self,
                        "路径不存在",
                        f"QMT数据路径不存在：\n{qmt_data_path}\n\n"
                        "请确认：\n"
                        "1. QMT客户端已正确安装\n"
                        "2. 数据路径配置正确\n"
                        "3. QMT客户端已启动并登录\n\n"
                        "是否仍要继续？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
            elif broker_name == "qmt-remote":
                # 远程QMT需要服务器配置
                server_host = self.config_manager.get("qmt_server_host")
                server_port = self.config_manager.get("qmt_server_port")
                server_token = self.config_manager.get("qmt_server_token")
                if not server_host or not server_port or not server_token:
                    QMessageBox.warning(
                        self,
                        "配置错误",
                        "使用远程QMT需要配置服务器信息！\n\n"
                        '请在"配置"页面中设置：\n'
                        "1. QMT服务器主机\n"
                        "2. QMT服务器端口\n"
                        "3. QMT服务器Token",
                    )
                    return

        # 确认对话框（根据券商类型显示不同提示）
        if broker_name == "simulator":
            confirm_msg = (
                "您确定要启动模拟交易吗？\n\n"
                "模拟交易不会使用真实资金，适合：\n"
                "1. 策略测试和验证\n"
                "2. 风控演练\n"
                "3. 系统联调\n\n"
                "继续吗？"
            )
            default_button = QMessageBox.StandardButton.Yes
        else:
            confirm_msg = (
                "您确定要启动实盘交易吗？\n\n"
                "实盘交易将使用真实资金进行交易，请确保：\n"
                "1. 策略已充分回测验证\n"
                "2. 已正确配置券商账户\n"
                "3. 已设置适当的风险控制\n"
            )
            if broker_name == "qmt":
                confirm_msg += "4. QMT客户端已启动并登录\n\n"
            confirm_msg += "继续吗？"
            default_button = QMessageBox.StandardButton.No
        
        reply = QMessageBox.warning(
            self,
            "确认启动" if broker_name == "simulator" else "确认启动实盘",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button,
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
        self.status_label.setStyleSheet(
            f"""
            font-weight: 600;
            padding: 8px;
            color: {COLORS['success']};
        """
        )
        self.log_text.clear()

        self.worker.start()

    def _stop_live(self):
        """停止实盘"""
        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止实盘交易吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait()
                self._append_log("实盘已停止")
                self._on_live_finished(1)

    def _append_log(self, message):
        """追加日志"""
        # GuiLogHandler 已经添加了时间戳，这里直接追加消息
        self.log_text.append(message)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _on_live_finished(self, exit_code):
        """实盘完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        self.status_label.setStyleSheet(
            f"""
            font-weight: 600;
            padding: 8px;
            color: {COLORS['text_secondary']};
        """
        )

    def is_running(self):
        """检查是否正在运行"""
        return self.worker is not None and self.worker.isRunning()

    def set_strategy_file(self, file_path: str):
        """设置策略文件（由主窗口调用）"""
        self.strategy_file_edit.setText(file_path)
