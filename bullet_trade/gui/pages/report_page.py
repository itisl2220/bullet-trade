"""
报告页面
"""

import os
from pathlib import Path
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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..theme import get_button_primary_style


class ReportPage(QWidget):
    """报告页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 参数配置组
        config_group = QGroupBox("报告生成")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(12)  # 设置表单行间距
        config_layout.setVerticalSpacing(12)  # 设置垂直间距
        
        # 回测结果目录
        result_layout = QHBoxLayout()
        self.result_dir_edit = QLineEdit()
        self.result_dir_edit.setPlaceholderText("选择回测结果目录...")
        result_layout.addWidget(self.result_dir_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_result_dir)
        result_layout.addWidget(browse_btn)
        config_layout.addRow("结果目录:", result_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("留空使用默认路径")
        output_layout.addWidget(self.output_file_edit)
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self._browse_output_file)
        output_layout.addWidget(output_browse_btn)
        config_layout.addRow("输出文件:", output_layout)
        
        # 报告格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(["html", "pdf"])
        config_layout.addRow("报告格式:", self.format_combo)
        
        # 报告标题
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("留空使用默认标题")
        config_layout.addRow("报告标题:", self.title_edit)
        
        layout.addWidget(config_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成报告")
        self.generate_btn.setStyleSheet(get_button_primary_style())
        self.generate_btn.clicked.connect(self._generate_report)
        button_layout.addWidget(self.generate_btn)
        
        self.open_btn = QPushButton("打开报告")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_report)
        button_layout.addWidget(self.open_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 信息显示
        info_group = QGroupBox("报告信息")
        info_layout = QVBoxLayout(info_group)
        self.info_text = QTextEdit()
        self.info_text.setFont(QFont("Consolas", 9))
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        layout.addWidget(info_group)
    
    def _browse_result_dir(self):
        """浏览结果目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择回测结果目录", self.result_dir_edit.text() or "./backtest_results"
        )
        if dir_path:
            self.result_dir_edit.setText(dir_path)
            # 自动填充输出文件
            if not self.output_file_edit.text():
                result_path = Path(dir_path)
                output_file = result_path / "report.html"
                self.output_file_edit.setText(str(output_file))
    
    def _browse_output_file(self):
        """浏览输出文件"""
        format_ext = self.format_combo.currentText()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存报告",
            self.output_file_edit.text() or f"report.{format_ext}",
            f"{format_ext.upper()}文件 (*.{format_ext});;所有文件 (*)"
        )
        if file_path:
            self.output_file_edit.setText(file_path)
    
    def _generate_report(self):
        """生成报告"""
        # 验证参数
        result_dir = self.result_dir_edit.text().strip()
        if not result_dir or not Path(result_dir).exists():
            QMessageBox.warning(self, "错误", "请选择有效的回测结果目录")
            return
        
        output_file = self.output_file_edit.text().strip()
        if not output_file:
            # 使用默认路径
            result_path = Path(result_dir)
            format_ext = self.format_combo.currentText()
            output_file = str(result_path / f"report.{format_ext}")
        
        try:
            from bullet_trade.core.analysis import generate_report, generate_html_report
            
            # 生成报告
            self.info_text.clear()
            self.info_text.append("正在生成报告...")
            
            # 根据格式生成不同类型的报告
            if self.format_combo.currentText() == "html":
                generate_html_report(
                    results_dir=result_dir,
                    output_file=output_file if output_file != result_dir else None,
                )
                report_file = output_file if output_file != result_dir else str(Path(result_dir) / "report.html")
            else:
                # PDF格式暂不支持，提示用户
                QMessageBox.warning(self, "提示", "PDF格式报告暂未实现，将生成HTML报告")
                generate_html_report(
                    results_dir=result_dir,
                    output_file=str(Path(result_dir) / "report.html"),
                )
                report_file = str(Path(result_dir) / "report.html")
            
            self.info_text.append(f"报告已生成: {report_file}")
            self.open_btn.setEnabled(True)
            self.open_btn.setProperty("report_file", report_file)
            
            QMessageBox.information(self, "成功", f"报告已生成:\n{report_file}")
        except Exception as e:
            error_msg = f"生成报告失败: {e}"
            self.info_text.append(error_msg)
            import traceback
            self.info_text.append(traceback.format_exc())
            QMessageBox.critical(self, "错误", error_msg)
    
    def _open_report(self):
        """打开报告"""
        report_file = self.open_btn.property("report_file")
        if report_file and Path(report_file).exists():
            import webbrowser
            webbrowser.open(f"file:///{Path(report_file).absolute()}")
        else:
            QMessageBox.warning(self, "错误", "报告文件不存在")

