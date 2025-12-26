"""
回测页面
"""

from pathlib import Path
from datetime import datetime
import hashlib
import logging
import webbrowser
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QDateEdit,
    QDoubleSpinBox,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QDialog,
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate, QUrl
from PyQt6.QtGui import QFont

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from ..theme import get_button_primary_style, get_log_text_style
from ..widgets.strategy_params_widget import StrategyParamsWidget


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
            import re

            msg = re.sub(r"\033\[[0-9;]*m", "", msg)
            self.signal.emit(msg)
        except Exception:
            pass  # 忽略错误，避免影响回测


class BacktestWorker(QThread):
    """回测工作线程"""

    finished = pyqtSignal(int)  # 退出码
    output = pyqtSignal(str)  # 输出消息
    report_ready = pyqtSignal(str)  # 报告文件路径

    def __init__(
        self,
        strategy_file,
        start_date,
        end_date,
        initial_cash,
        frequency,
        benchmark,
        output_dir,
        generate_images,
        generate_csv,
        generate_html,
        data_provider=None,
        strategy_params=None,
    ):
        super().__init__()
        self.strategy_file = strategy_file
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.frequency = frequency
        self.benchmark = benchmark
        self.output_dir = output_dir
        self.generate_images = generate_images
        self.generate_csv = generate_csv
        self.generate_html = generate_html
        self.data_provider = data_provider
        self.strategy_params = strategy_params or {}

    def run(self):
        """运行回测"""
        gui_handler = None
        try:
            # 设置数据提供者（如果指定）
            if self.data_provider:
                from bullet_trade.data.api import set_data_provider

                self.output.emit(f"设置数据源: {self.data_provider}")
                set_data_provider(self.data_provider)

            # 添加GUI日志处理器，将日志重定向到GUI
            from bullet_trade.core.globals import log

            gui_handler = GuiLogHandler(self.output)
            gui_handler.setLevel(logging.INFO)
            log.logger.addHandler(gui_handler)

            # 同时添加到bullet_trade logger（确保所有模块的日志都能显示）
            bullet_trade_logger = logging.getLogger("bullet_trade")
            bullet_trade_logger.addHandler(gui_handler)

            from bullet_trade.core.engine import BacktestEngine

            engine = BacktestEngine(
                strategy_file=self.strategy_file,
                start_date=self.start_date,
                end_date=self.end_date,
                frequency=self.frequency,
                initial_cash=self.initial_cash,
                benchmark=self.benchmark,
                log_file=str(Path(self.output_dir) / "backtest.log"),
                strategy_params=self.strategy_params,
            )

            self.output.emit("开始回测...")
            # 运行回测并获取结果
            results = engine.run()

            # 生成报告
            if self.generate_csv or self.generate_html:
                self.output.emit("生成报告...")
                from bullet_trade.core.analysis import generate_report

                # 传递results参数，这样会先保存CSV文件再生成报告
                generate_report(
                    results=results,
                    output_dir=self.output_dir,
                    gen_csv=self.generate_csv,
                    gen_html=self.generate_html,
                    gen_images=self.generate_images,
                )

            self.output.emit("回测完成！")

            # 发送报告文件路径信号
            if self.generate_html:
                report_file = str(Path(self.output_dir) / "report.html")
                if Path(report_file).exists():
                    self.report_ready.emit(report_file)

            self.finished.emit(0)
        except Exception as e:
            self.output.emit(f"错误: {e}")
            import traceback

            self.output.emit(traceback.format_exc())
            self.finished.emit(1)
        finally:
            # 清理GUI日志处理器
            if gui_handler:
                try:
                    from bullet_trade.core.globals import log

                    log.logger.removeHandler(gui_handler)
                    bullet_trade_logger = logging.getLogger("bullet_trade")
                    bullet_trade_logger.removeHandler(gui_handler)
                except Exception:
                    pass


class BacktestPage(QWidget):
    """回测页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        # 主布局：左右分栏
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧区域：表单和控制（占1/3）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 参数配置组
        config_group = QGroupBox("回测参数")
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
        select_remote_btn = QPushButton("从远端选择...")
        select_remote_btn.clicked.connect(self._open_remote_selector)
        strategy_layout.addWidget(select_remote_btn)
        config_layout.addRow("策略文件:", strategy_layout)

        # 回测日期
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.start_date_edit.setCalendarPopup(True)
        config_layout.addRow("开始日期:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        config_layout.addRow("结束日期:", self.end_date_edit)

        # 初始资金
        self.cash_spin = QDoubleSpinBox()
        self.cash_spin.setRange(1000, 100000000)
        self.cash_spin.setValue(100000)
        self.cash_spin.setDecimals(0)
        self.cash_spin.setSuffix(" 元")
        config_layout.addRow("初始资金:", self.cash_spin)

        # 回测频率
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["day", "minute"])
        config_layout.addRow("回测频率:", self.frequency_combo)

        # 数据源选择
        self.data_provider_combo = QComboBox()
        self.data_provider_combo.addItems(["jqdata", "qmt", "miniqmt", "tushare"])
        self.data_provider_combo.setCurrentText("jqdata")
        self.data_provider_combo.setToolTip(
            "jqdata: 聚宽数据源（需要账号）\n"
            "qmt/miniqmt: QMT本地行情数据\n"
            "tushare: Tushare数据源（需要token）"
        )
        config_layout.addRow("数据源:", self.data_provider_combo)

        # 基准指数
        self.benchmark_edit = QLineEdit()
        self.benchmark_edit.setPlaceholderText("如: 000300.XSHG (可选)")
        config_layout.addRow("基准指数:", self.benchmark_edit)

        # 输出目录（只显示基础目录，实际会生成唯一子目录）
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText("./backtest_results")
        self.output_dir_edit.setPlaceholderText("基础输出目录（会自动创建唯一子目录）")
        output_layout.addWidget(self.output_dir_edit)
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(output_browse_btn)
        config_layout.addRow("输出目录:", output_layout)

        # 报告选项
        self.generate_csv_check = QComboBox()
        self.generate_csv_check.addItems(["是", "否"])
        self.generate_csv_check.setCurrentIndex(0)
        config_layout.addRow("导出CSV:", self.generate_csv_check)

        self.generate_html_check = QComboBox()
        self.generate_html_check.addItems(["是", "否"])
        self.generate_html_check.setCurrentIndex(0)
        config_layout.addRow("生成HTML:", self.generate_html_check)

        self.generate_images_check = QComboBox()
        self.generate_images_check.addItems(["否", "是"])
        self.generate_images_check.setCurrentIndex(0)
        config_layout.addRow("生成图片:", self.generate_images_check)

        left_layout.addWidget(config_group)

        # 策略参数配置
        self.params_widget = StrategyParamsWidget()
        self.params_widget.setMinimumHeight(250)  # 设置最小高度
        left_layout.addWidget(self.params_widget, 1)  # 设置拉伸因子，使其占据更多空间

        # 当策略文件改变时，加载参数
        self.strategy_file_edit.textChanged.connect(self._on_strategy_file_changed)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始回测")
        self.start_btn.setStyleSheet(get_button_primary_style())
        self.start_btn.clicked.connect(self._start_backtest)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_backtest)
        button_layout.addWidget(self.stop_btn)

        button_layout.addStretch()
        left_layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        left_layout.addStretch()  # 添加弹性空间，使内容靠上

        # 右侧区域：日志（占2/3）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 输出日志
        log_group = QGroupBox("回测日志")
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
            self._on_strategy_file_changed()

    def _open_remote_selector(self):
        """打开远端策略选择对话框（与 StrategyPage 类似）"""
        dlg = QDialog(self)
        dlg.setWindowTitle("选择远端策略")
        layout = QVBoxLayout(dlg)
        listw = QListWidget()
        layout.addWidget(listw)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        select_btn = QPushButton("选择")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def refresh():
            listw.clear()
            try:
                from ..gui.config_manager import ConfigManager  # type: ignore
            except Exception:
                pass
            try:
                from ..config_manager import ConfigManager as CM  # fallback
                cm = CM()
                server = cm.get("strategy_server_url", None)
                if not server:
                    host = cm.get("qmt_server_host", "127.0.0.1")
                    port = cm.get("qmt_server_port", 58620)
                    server = f"http://{host}:{port}"
                token = cm.get("qmt_server_token", "") or os.getenv("STRATEGY_API_TOKEN") or os.getenv("BT_API_TOKEN")
            except Exception:
                server = os.getenv("STRATEGY_SERVER_URL") or os.getenv("BT_SERVER_URL") or "http://127.0.0.1:3000"
                token = os.getenv("STRATEGY_API_TOKEN") or os.getenv("BT_API_TOKEN")
            url = server.rstrip("/") + "/api/strategies"
            import requests
            try:
                headers = {"Accept": "application/json"}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    for item in data:
                        sid = item.get("id", "")
                        name = item.get("name", "")
                        listw.addItem(f"{sid}  {name}")
            except Exception as e:
                QMessageBox.warning(self, "请求失败", f"无法获取远端策略: {e}")

        def select_item():
            it = listw.currentItem()
            if not it:
                QMessageBox.warning(self, "提示", "请先选择一项")
                return
            text = it.text()
            sid = text.split()[0]
            remote = f"remote://{sid}"
            self.strategy_file_edit.setText(remote)
            dlg.accept()

        refresh_btn.clicked.connect(lambda: refresh())
        select_btn.clicked.connect(lambda: select_item())
        cancel_btn.clicked.connect(dlg.reject)
        refresh()
        dlg.exec()

    def _on_strategy_file_changed(self):
        """策略文件改变时的处理"""
        strategy_file = self.strategy_file_edit.text().strip()
        if strategy_file and Path(strategy_file).exists():
            self.params_widget.load_strategy_params(strategy_file)

    def _browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def _start_backtest(self):
        """开始回测"""
        # 验证参数
        strategy_file = self.strategy_file_edit.text().strip()
        if not strategy_file or not Path(strategy_file).exists():
            QMessageBox.warning(self, "错误", "请选择有效的策略文件")
            return

        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        if start_date >= end_date:
            QMessageBox.warning(self, "错误", "开始日期必须早于结束日期")
            return

        base_output_dir = self.output_dir_edit.text().strip()
        if not base_output_dir:
            QMessageBox.warning(self, "错误", "请指定输出目录")
            return

        # 生成唯一的输出目录名（基于时间戳和策略文件名）
        strategy_name = Path(strategy_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 使用策略文件名和时间戳生成唯一标识
        unique_id = hashlib.md5(f"{strategy_name}_{timestamp}".encode()).hexdigest()[:8]
        unique_dir_name = f"{timestamp}_{unique_id}"

        # 创建唯一的结果目录
        output_dir = str(Path(base_output_dir).expanduser() / unique_dir_name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        self._append_log(f"结果将保存到: {output_dir}")

        # 获取数据源
        data_provider = self.data_provider_combo.currentText().strip()
        if data_provider == "miniqmt":
            data_provider = "qmt"  # miniqmt 和 qmt 是同一个提供者

        # 获取策略参数
        strategy_params = self.params_widget.get_params()

        # 启动工作线程
        self.worker = BacktestWorker(
            strategy_file=strategy_file,
            start_date=start_date,
            end_date=end_date,
            initial_cash=self.cash_spin.value(),
            frequency=self.frequency_combo.currentText(),
            benchmark=self.benchmark_edit.text().strip() or None,
            output_dir=output_dir,
            generate_images=self.generate_images_check.currentIndex() == 1,
            generate_csv=self.generate_csv_check.currentIndex() == 0,
            generate_html=self.generate_html_check.currentIndex() == 0,
            data_provider=(
                data_provider if data_provider != "jqdata" else None
            ),  # jqdata是默认，不需要设置
            strategy_params=strategy_params,
        )

        self.worker.output.connect(self._append_log)
        self.worker.finished.connect(self._on_backtest_finished)
        self.worker.report_ready.connect(self._show_report)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.log_text.clear()

        # 保存输出目录供后续使用
        self.current_output_dir = output_dir

        self.worker.start()

    def _stop_backtest(self):
        """停止回测"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self._append_log("回测已停止")
            self._on_backtest_finished(1)

    def _append_log(self, message):
        """追加日志"""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _on_backtest_finished(self, exit_code):
        """回测完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        if exit_code == 0:
            output_dir = getattr(self, "current_output_dir", "未知")
            self._append_log(f"回测结果已保存到: {output_dir}")
        else:
            QMessageBox.warning(self, "错误", "回测过程中出现错误，请查看日志")

    def _show_report(self, report_file: str):
        """显示报告窗口"""
        # 使用系统默认浏览器打开报告文件（回退到外部浏览器打开）
        report_path = Path(report_file).absolute()
        try:
            webbrowser.open(report_path.as_uri())
            self._append_log(f"已在默认浏览器中打开报告: {report_file}")
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法在浏览器中打开报告: {e}")

    def set_strategy_file(self, file_path: str):
        """设置策略文件（由主窗口调用）"""
        self.strategy_file_edit.setText(file_path)
        self._on_strategy_file_changed()
