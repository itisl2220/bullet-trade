"""
参数优化页面
"""

import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QDateEdit,
    QGroupBox,
    QFormLayout,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from ..theme import get_button_primary_style, get_log_text_style
from ..message_helper import show_info, show_warning, show_error, show_confirm


class OptimizeWorker(QThread):
    """参数优化工作线程"""

    finished = pyqtSignal(int)
    output = pyqtSignal(str)
    result_ready = pyqtSignal(str)  # 结果文件路径

    def __init__(self, strategy_file, params_file, start_date, end_date, output_file, processes):
        super().__init__()
        self.strategy_file = strategy_file
        self.params_file = params_file
        self.start_date = start_date
        self.end_date = end_date
        self.output_file = output_file
        self.processes = processes

    def run(self):
        """运行优化"""
        try:
            from bullet_trade.core.optimizer import run_param_grid
            from bullet_trade.cli.optimize import _process_param_grid

            # 读取参数配置
            with open(self.params_file, "r", encoding="utf-8") as f:
                params_config = json.load(f)

            # 提取参数网格
            param_grid_raw = params_config.get("param_grid", {})
            if not param_grid_raw:
                raise ValueError("参数文件中未找到 'param_grid' 配置")

            # 处理 Python 表达式
            param_grid = _process_param_grid(param_grid_raw)

            self.output.emit("开始参数优化...")

            # 运行参数优化
            run_param_grid(
                strategy_file=self.strategy_file,
                start_date=self.start_date,
                end_date=self.end_date,
                param_grid=param_grid,
                processes=self.processes,
                output_csv=self.output_file,
            )

            self.output.emit(f"优化完成！结果已保存到: {self.output_file}")
            self.result_ready.emit(self.output_file)
            self.finished.emit(0)
        except Exception as e:
            self.output.emit(f"错误: {e}")
            import traceback

            self.output.emit(traceback.format_exc())
            self.finished.emit(1)


class OptimizePage(QWidget):
    """参数优化页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 参数配置组
        config_group = QGroupBox("优化参数")
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

        # 参数配置文件
        params_layout = QHBoxLayout()
        self.params_file_edit = QLineEdit()
        self.params_file_edit.setPlaceholderText("选择参数配置文件 (JSON)...")
        params_layout.addWidget(self.params_file_edit)
        params_browse_btn = QPushButton("浏览...")
        params_browse_btn.clicked.connect(self._browse_params_file)
        params_layout.addWidget(params_browse_btn)
        create_params_btn = QPushButton("创建模板")
        create_params_btn.clicked.connect(self._create_params_template)
        params_layout.addWidget(create_params_btn)
        config_layout.addRow("参数配置:", params_layout)

        # 回测日期
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.start_date_edit.setCalendarPopup(True)
        config_layout.addRow("开始日期:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        config_layout.addRow("结束日期:", self.end_date_edit)

        # 输出文件
        output_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setText("./optimization_results.csv")
        output_layout.addWidget(self.output_file_edit)
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self._browse_output_file)
        output_layout.addWidget(output_browse_btn)
        config_layout.addRow("输出文件:", output_layout)

        # 进程数
        self.processes_edit = QLineEdit()
        self.processes_edit.setPlaceholderText("留空使用CPU核心数")
        config_layout.addRow("并行进程数:", self.processes_edit)

        layout.addWidget(config_group)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始优化")
        self.start_btn.setStyleSheet(get_button_primary_style())
        self.start_btn.clicked.connect(self._start_optimize)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_optimize)
        button_layout.addWidget(self.stop_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 输出日志
        log_group = QGroupBox("优化日志")
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
            self,
            "选择策略文件",
            str(Path.home()),
            "Python文件 (*.py);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            self.strategy_file_edit.setText(file_path)

    def _browse_params_file(self):
        """浏览参数配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择参数配置文件",
            str(Path.home()),
            "JSON文件 (*.json);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            self.params_file_edit.setText(file_path)

    def _browse_output_file(self):
        """浏览输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存优化结果",
            self.output_file_edit.text(),
            "CSV文件 (*.csv);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            self.output_file_edit.setText(file_path)

    def _create_params_template(self):
        """创建参数配置模板"""
        template = {
            "param1": [1, 2, 3, 4, 5],
            "param2": [0.1, 0.2, 0.3],
            "param3": "py:range(10, 20, 2)",
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存参数模板",
            "params_template.json",
            "JSON文件 (*.json);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                self.params_file_edit.setText(file_path)
                show_info(self, "参数模板已创建", title="成功")
            except Exception as e:
                show_error(self, f"无法创建模板: {e}", title="错误")

    def _start_optimize(self):
        """开始优化"""
        # 验证参数
        strategy_file = self.strategy_file_edit.text().strip()
        if not strategy_file or not Path(strategy_file).exists():
            show_warning(self, "请选择有效的策略文件", title="错误")
            return

        params_file = self.params_file_edit.text().strip()
        if not params_file or not Path(params_file).exists():
            show_warning(self, "请选择有效的参数配置文件", title="错误")
            return

        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        if start_date >= end_date:
            show_warning(self, "开始日期必须早于结束日期", title="错误")
            return

        output_file = self.output_file_edit.text().strip()
        if not output_file:
            show_warning(self, "请指定输出文件", title="错误")
            return

        # 解析进程数
        processes = None
        processes_str = self.processes_edit.text().strip()
        if processes_str:
            try:
                processes = int(processes_str)
                if processes < 1:
                    raise ValueError
            except ValueError:
                show_warning(self, "进程数必须是正整数", title="错误")
                return

        # 启动工作线程
        self.worker = OptimizeWorker(
            strategy_file=strategy_file,
            params_file=params_file,
            start_date=start_date,
            end_date=end_date,
            output_file=output_file,
            processes=processes,
        )

        self.worker.output.connect(self._append_log)
        self.worker.finished.connect(self._on_optimize_finished)
        self.worker.result_ready.connect(self._on_result_ready)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_text.clear()

        self.worker.start()

    def _stop_optimize(self):
        """停止优化"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self._append_log("优化已停止")
            self._on_optimize_finished(1)

    def _append_log(self, message):
        """追加日志"""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _on_optimize_finished(self, exit_code):
        """优化完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if exit_code == 0:
            show_info(self, "参数优化完成！", title="成功")
        else:
            show_warning(self, "优化过程中出现错误，请查看日志", title="错误")

    def _on_result_ready(self, result_file):
        """结果就绪"""
        self._append_log(f"结果文件: {result_file}")

    def set_strategy_file(self, file_path: str):
        """设置策略文件（由主窗口调用）"""
        self.strategy_file_edit.setText(file_path)
