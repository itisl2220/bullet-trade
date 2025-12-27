"""
回测页面
"""

from pathlib import Path
from datetime import datetime
import hashlib
import logging
import os
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
    QListWidget,
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from ..theme import COLORS, get_button_primary_style, get_log_text_style
from ..widgets.strategy_params_widget import StrategyParamsWidget
from ..message_helper import show_info, show_warning, show_error, show_confirm


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
        auth_manager=None,
        decrypted_source=None,
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
        self.auth_manager = auth_manager
        # 如果通过 UI 直接加载了远程解密源码，可以通过这个字段传入给工作线程
        self.decrypted_source = decrypted_source

    def run(self):
        """运行回测"""
        gui_handler = None
        try:
            self.output.emit("BacktestWorker.run() 开始执行")
            # 设置数据提供者（如果指定）- 在内存策略和文件策略分支之前统一设置
            self.output.emit(
                f"BacktestWorker data_provider 参数: {repr(self.data_provider)}, 类型: {type(self.data_provider)}"
            )
            self.output.emit(
                f"decrypted_source 存在: {isinstance(self.decrypted_source, str) and bool(self.decrypted_source)}"
            )
            if self.data_provider:
                from bullet_trade.data.api import set_data_provider, get_data_provider

                self.output.emit(f"准备设置数据源: {self.data_provider}")
                try:
                    set_data_provider(self.data_provider)
                    self.output.emit(f"set_data_provider('{self.data_provider}') 调用完成")
                except Exception as e:
                    # 记录更详细的认证/初始化错误，便于排查为什么回退到 jqdata
                    self.output.emit(f"设置数据源失败: {e}")
                    import traceback

                    self.output.emit(f"设置数据源失败详情: {traceback.format_exc()}")
                    raise  # 重新抛出异常，让用户知道数据源设置失败

                # 立即读取并输出当前 provider 的详细信息
                try:
                    prov = get_data_provider()
                    pname = getattr(prov, "name", prov.__class__.__name__)
                    cname = prov.__class__.__name__
                    self.output.emit(f"设置后数据提供者类名: {cname}, name属性: {pname}")
                    # 如果 provider 有 config/host 等属性，尽量显示关键信息用于排查
                    info_parts = [f"class={cname}", f"name={pname}"]
                    cfg = getattr(prov, "config", None)
                    if isinstance(cfg, dict):
                        for key in ("host", "port", "token", "source", "data_dir"):
                            if cfg.get(key) is not None:
                                info_parts.append(f"{key}={cfg.get(key)}")
                    self.output.emit(f"当前数据提供者详情: {', '.join(info_parts)}")
                except Exception as e:
                    self.output.emit(f"读取当前数据提供者失败: {e}")
                    import traceback

                    self.output.emit(f"读取数据提供者失败详情: {traceback.format_exc()}")
            else:
                self.output.emit("未指定数据提供者，使用默认")

            # 设置GUI日志处理器，将日志重定向到GUI（在分支判断之前统一设置）
            gui_handler = GuiLogHandler(self.output)
            gui_handler.setLevel(logging.INFO)

            # 添加到全局log logger
            from bullet_trade.core.globals import log

            log.logger.addHandler(gui_handler)

            # 同时添加到bullet_trade logger（确保所有模块的日志都能显示）
            bullet_trade_logger = logging.getLogger("bullet_trade")
            bullet_trade_logger.addHandler(gui_handler)

            # 如果外部已经传入了解密后的源码（UI 直接下载并解密），优先在内存中注入执行，避免写临时文件
            if isinstance(self.decrypted_source, str) and self.decrypted_source:
                import types

                # 将源码编译并注入为模块，提取 initialize/handle_data 等函数并传给引擎
                self.output.emit("使用内存中解密后的策略源码，准备注入回测引擎...")
                module_name = "strategy_remote_inject"
                strategy_module = types.ModuleType(module_name)

                # 预先导入常用的数据源依赖到策略模块的命名空间
                # 这样策略代码中的 `from jqdata import *` 或 `import jqdatasdk` 就能正常工作
                try:
                    # 导入 jqdatasdk 并作为 jqdata 暴露给策略
                    # 为了支持 `from jqdata import *`，需要创建一个 jqdata 模块并注册到 sys.modules
                    import jqdatasdk
                    import sys
                    import types

                    # 创建一个代理模块来模拟 jqdata
                    jqdata_module = types.ModuleType('jqdata')

                    # 将 jqdatasdk 的所有公开属性复制到 jqdata 模块
                    jqdata_public_attrs = [
                        name for name in dir(jqdatasdk)
                        if not name.startswith('_')
                    ]

                    for attr_name in jqdata_public_attrs:
                        try:
                            attr = getattr(jqdatasdk, attr_name)
                            setattr(jqdata_module, attr_name, attr)
                        except (AttributeError, TypeError):
                            pass

                    # 关键：将 jqdata 模块注册到 sys.modules
                    # 这样 `from jqdata import *` 就能找到它
                    sys.modules['jqdata'] = jqdata_module

                    # 同时也注入到策略模块的命名空间（兼容其他导入方式）
                    strategy_module.jqdata = jqdata_module
                    strategy_module.jqdatasdk = jqdatasdk

                    # 创建聚宽平台的全局上下文对象 g
                    class G:
                        pass
                    strategy_module.g = G()

                    # 添加聚宽平台的兼容函数
                    # 这些函数在聚宽平台是内置的，我们需要提供模拟实现
                    def set_benchmark(security):
                        """设置基准（聚宽兼容函数）"""
                        # 这个函数实际上不需要做什么，因为基准已经在引擎中设置
                        self.output.emit(f"策略设置基准: {security}")
                        return True

                    def run_daily(func, time=None):
                        """每日定时运行（聚宽兼容函数）"""
                        # 这个函数实际上不需要做什么，因为定时由引擎控制
                        self.output.emit(f"策略设置定时任务: {func.__name__} at {time}")
                        # 不做任何事，让引擎自然调用

                    def order(security, amount):
                        """下单（聚宽兼容函数）"""
                        # 这个函数会在后续的引擎调用中真正实现
                        # 这里只是占位，实际下单由引擎处理
                        self.output.emit(f"策略调用 order({security}, {amount})")
                        # 返回模拟订单ID
                        return f"mock_order_{security}_{amount}"

                    # 将这些函数注入到策略模块
                    strategy_module.set_benchmark = set_benchmark
                    strategy_module.run_daily = run_daily
                    strategy_module.order = order

                    # 导入其他常用依赖
                    import pandas as pd
                    import numpy as np
                    strategy_module.pd = pd
                    strategy_module.numpy = np
                    strategy_module.np = np

                    # 导入时间处理
                    from datetime import datetime, timedelta, date
                    strategy_module.datetime = datetime
                    strategy_module.timedelta = timedelta
                    strategy_module.date = date

                    self.output.emit(f"已预加载策略依赖: jqdatasdk (包含 {len(jqdata_public_attrs)} 个公开属性), pandas, numpy, datetime, 以及聚宽兼容函数 (set_benchmark, run_daily, order, g)")
                except ImportError as e:
                    self.output.emit(f"警告: 部分依赖预加载失败: {e}")

                try:
                    # 现在 exec 执行时，`from jqdata import *` 就能正常工作了
                    # 不使用 compile()，直接 exec 字符串，避免编译时检查导入
                    exec(self.decrypted_source, strategy_module.__dict__)
                except Exception as e:
                    raise Exception(f"执行解密后源码失败: {e}")
                finally:
                    # 清理：从 sys.modules 中移除 jqdata 模块
                    # 避免污染全局模块系统
                    if 'jqdata' in sys.modules:
                        del sys.modules['jqdata']

                init_fn = getattr(strategy_module, "initialize", None)
                handle_fn = getattr(strategy_module, "handle_data", None)
                before_fn = getattr(strategy_module, "before_trading_start", None)
                after_fn = getattr(strategy_module, "after_trading_end", None)
                process_init_fn = getattr(strategy_module, "process_initialize", None)

                from bullet_trade.core.analysis import generate_report
                from bullet_trade.core.engine import BacktestEngine

                engine = BacktestEngine(
                    strategy_file=None,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    frequency=self.frequency,
                    initial_cash=self.initial_cash,
                    benchmark=self.benchmark,
                    log_file=str(Path(self.output_dir) / "backtest.log"),
                    initialize=init_fn,
                    handle_data=handle_fn,
                    before_trading_start=before_fn,
                    after_trading_end=after_fn,
                    process_initialize=process_init_fn,
                    strategy_params=self.strategy_params,
                )

                self.output.emit("开始回测（内存策略）...")
                results = engine.run()

                if self.generate_csv or self.generate_html:
                    self.output.emit("生成报告...")
                    generate_report(
                        results=results,
                        output_dir=self.output_dir,
                        gen_csv=self.generate_csv,
                        gen_html=self.generate_html,
                        gen_images=self.generate_images,
                    )

                self.output.emit("回测完成！")
                if self.generate_html:
                    report_file = str(Path(self.output_dir) / "report.html")
                    if Path(report_file).exists():
                        self.report_ready.emit(report_file)
                self.finished.emit(0)
                return

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

    def __init__(self, auth_manager=None, parent=None):
        """
        auth_manager: 可选的 AuthManager，用于访问远端策略服务
        """
        super().__init__(parent)
        self.auth_manager = auth_manager
        # 如果提供了 auth_manager，则可创建 StrategyManager（按需）
        try:
            from ..strategy_manager import StrategyManager

            self.strategy_manager = StrategyManager(auth_manager)  # type: ignore
        except Exception:
            self.strategy_manager = None

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
            self,
            "选择策略文件",
            str(Path.home()),
            "Python文件 (*.py);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            self.strategy_file_edit.setText(file_path)
            self._on_strategy_file_changed()

    def _open_remote_selector(self):
        """打开远端策略选择对话框（与 StrategyPage 类似）"""
        dlg = QDialog(self)
        dlg.setWindowTitle("选择远端策略")
        dlg.setMinimumSize(600, 450)
        dlg.setStyleSheet(
            f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
            }}
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 6px;
                padding: 8px;
                font-family: Microsoft YaHei UI, Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }}
            QListWidget::item {{
                color: {COLORS['text_primary']};
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_white']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['primary_hover']};
                color: {COLORS['text_white']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_white']};
                border: none;
                border-radius: 6px;
                padding: 6px 24px;
                min-width: 90px;
                min-height: 28px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:cancel {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_medium']};
            }}
            QPushButton:cancel:hover {{
                background-color: {COLORS['bg_tertiary']};
                border-color: {COLORS['primary']};
            }}
        """
        )
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        listw = QListWidget()
        layout.addWidget(listw)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        refresh_btn = QPushButton("刷新")
        select_btn = QPushButton("选择")
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("cancel", True)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(select_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def refresh():
            listw.clear()
            # 优先使用已登录的 APIClient（通过 AuthManager）获取策略列表，避免手动拼接 URL 导致端口/host 配置不一致
            try:
                api_client = None
                if getattr(self, "auth_manager", None) and getattr(
                    self.auth_manager, "api_client", None
                ):
                    api_client = self.auth_manager.api_client

                if api_client:
                    success, data = api_client.get_strategies()
                    if not success:
                        raise Exception(data)
                    if isinstance(data, list):
                        for item in data:
                            sid = (
                                item.get("id", "")
                                if isinstance(item, dict)
                                else getattr(item, "id", "")
                            )
                            name = (
                                item.get("name", "")
                                if isinstance(item, dict)
                                else getattr(item, "name", "")
                            )
                            listw.addItem(f"{sid}  {name}")
                    else:
                        raise Exception("后端返回格式异常")
                else:
                    # 回退到原始的基于配置的请求方式
                    from ..config_manager import ConfigManager as CM  # fallback

                    cm = CM()
                    server = cm.get("strategy_server_url", None)
                    if not server:
                        host = cm.get("qmt_server_host", "127.0.0.1")
                        port = cm.get("qmt_server_port", 58620)
                        server = f"http://{host}:{port}"
                    token = (
                        cm.get("qmt_server_token", "")
                        or os.getenv("STRATEGY_API_TOKEN")
                        or os.getenv("BT_API_TOKEN")
                    )
                    url = server.rstrip("/") + "/api/strategies"
                    import requests

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
                # 更友好的错误提示，给出可能的原因和排查建议
                msg = f"无法获取远端策略: {e}\n\n可能原因：策略服务器未运行、主机/端口配置错误或网络被阻止。请检查设置并确认服务器可达。"
                show_warning(self, msg, title="请求失败")

        def select_item():
            it = listw.currentItem()
            if not it:
                show_warning(self, "请先选择一项")
                return
            text = it.text()
            sid = text.split()[0]
            # 直接从服务器下载并解密策略，然后加载到编辑器（不使用 remote:// 协议）
            try:
                decrypted_code = None

                # 优先使用 auth_manager.api_client 下载并解密
                if getattr(self, "auth_manager", None) and getattr(
                    self.auth_manager, "api_client", None
                ):
                    api_client = self.auth_manager.api_client
                    success, encrypted = api_client.download_strategy(sid)
                    if not success:
                        raise Exception(encrypted)
                    success, key_data = api_client.get_strategy_key(sid)
                    if not success:
                        raise Exception(key_data)
                    key_b64 = key_data.get("key_b64") if isinstance(key_data, dict) else None
                    if not key_b64:
                        raise Exception("无法获取解密密钥")
                    # 解密（与 StrategyManager._decrypt_strategy 兼容）
                    import base64
                    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

                    key = base64.b64decode(key_b64)
                    if len(encrypted) < 12 + 16:
                        raise Exception("加密数据格式异常")
                    nonce = encrypted[:12]
                    tag = encrypted[-16:]
                    ciphertext = encrypted[12:-16]
                    aesgcm = AESGCM(key)
                    plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)
                    decrypted_code = plaintext.decode("utf-8")
                elif getattr(self, "strategy_manager", None):
                    # 使用 strategy_manager 下载（只验证，不返回代码）
                    success = self.strategy_manager.download_strategy(sid)
                    if not success:
                        raise Exception("下载或验证策略失败")
                    # 从 strategy_manager 获取加密数据和密钥
                    if hasattr(self.strategy_manager, 'downloaded_strategies') and sid in self.strategy_manager.downloaded_strategies:
                        # 使用已下载的加密数据
                        import base64
                        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

                        success, encrypted = api_client.download_strategy(sid)
                        if not success:
                            raise Exception("重新下载策略失败")
                        success, key_data = api_client.get_strategy_key(sid)
                        if not success:
                            raise Exception("获取密钥失败")
                        key_b64 = key_data.get("key_b64") if isinstance(key_data, dict) else None
                        key = base64.b64decode(key_b64)
                        nonce = encrypted[:12]
                        tag = encrypted[-16:]
                        ciphertext = encrypted[12:-16]
                        aesgcm = AESGCM(key)
                        plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)
                        decrypted_code = plaintext.decode("utf-8")
                    else:
                        raise Exception("策略未下载，请先下载策略")
                else:
                    raise Exception("无法下载策略：未提供 AuthManager 或 StrategyManager")

                # 将解密后的策略源码加载到内存，供回测直接注入执行（不写临时文件）
                if decrypted_code is not None:
                    # 保存解密源码到页面实例
                    self.decrypted_strategy_source = decrypted_code
                    # 清空路径输入以表明当前为内存策略
                    self.strategy_file_edit.setText("")
                    # 直接从源码加载参数到参数面板
                    try:
                        self.params_widget.load_strategy_params_from_source(decrypted_code)
                    except Exception:
                        # 失败时清空旧参数
                        self.params_widget._clear_params()
                    show_info(
                        self,
                        "远端策略已下载并解密，已加载到内存（启动回测时将直接注入执行）。",
                    )
                    dlg.accept()
                else:
                    raise Exception("解密后策略内容为空")
            except Exception as e:
                show_warning(self, f"无法下载或解密远端策略: {e}", title="下载失败")

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
            self,
            "选择输出目录",
            self.output_dir_edit.text(),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def _start_backtest(self):
        """开始回测"""
        # 验证参数
        strategy_file = self.strategy_file_edit.text().strip()
        # 支持内存中解密后的策略：如果没有本地文件，但存在 decrypted_strategy_source 则允许
        if not strategy_file or not Path(strategy_file).exists():
            if not getattr(self, "decrypted_strategy_source", None):
                show_warning(self, "请选择有效的策略文件或先从远端加载策略", title="错误")
                return

        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        if start_date >= end_date:
            show_warning(self, "开始日期必须早于结束日期", title="错误")
            return

        base_output_dir = self.output_dir_edit.text().strip()
        if not base_output_dir:
            show_warning(self, "请指定输出目录", title="错误")
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
        self._append_log(f"用户选择的 data_provider: {repr(data_provider)}")
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
            decrypted_source=getattr(self, "decrypted_strategy_source", None),
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
            show_warning(self, "回测过程中出现错误，请查看日志", title="错误")

    def _show_report(self, report_file: str):
        """显示报告窗口"""
        # 使用系统默认浏览器打开报告文件（回退到外部浏览器打开）
        report_path = Path(report_file).absolute()
        try:
            webbrowser.open(report_path.as_uri())
            self._append_log(f"已在默认浏览器中打开报告: {report_file}")
        except Exception as e:
            show_warning(self, f"无法在浏览器中打开报告: {e}", title="打开失败")

    def set_strategy_file(self, file_path: str):
        """设置策略文件（由主窗口调用）"""
        self.strategy_file_edit.setText(file_path)
        self._on_strategy_file_changed()
