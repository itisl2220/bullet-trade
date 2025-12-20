"""
策略管理页面
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
)
from PyQt6.QtGui import QFont

from ..theme import get_code_editor_style


class StrategyPage(QWidget):
    """策略管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 工具栏
        toolbar = QHBoxLayout()

        self.open_btn = QPushButton("打开策略文件")
        self.open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(self.open_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_file)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)

        self.save_as_btn = QPushButton("另存为")
        self.save_as_btn.clicked.connect(self._save_as_file)
        self.save_as_btn.setEnabled(False)
        toolbar.addWidget(self.save_as_btn)

        toolbar.addStretch()

        self.file_label = QLabel("未选择文件")
        toolbar.addWidget(self.file_label)

        layout.addLayout(toolbar)

        # 代码编辑器
        editor_group = QGroupBox("策略代码")
        editor_layout = QVBoxLayout(editor_group)
        
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet(get_code_editor_style())
        self.code_editor.textChanged.connect(self._on_text_changed)
        editor_layout.addWidget(self.code_editor)
        
        layout.addWidget(editor_group)
        
        # 提示信息
        from ..theme import COLORS
        info_label = QLabel(
            "提示：策略文件应包含 initialize(context) 函数，"
            "可选包含 handle_data(context, data)、before_trading_start(context) 等函数"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 8px;")
        layout.addWidget(info_label)

    def _on_text_changed(self):
        """文本改变时启用保存按钮"""
        self.save_btn.setEnabled(True)
        self.save_as_btn.setEnabled(True)

    def _open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择策略文件", str(Path.home()), "Python文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            self.load_strategy_file(file_path)

    def load_strategy_file(self, file_path: str):
        """加载策略文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.code_editor.setPlainText(content)
            self.current_file = file_path
            self.file_label.setText(f"文件: {Path(file_path).name}")
            self.save_btn.setEnabled(False)
            self.save_as_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {e}")

    def _save_file(self):
        """保存文件"""
        if not self.current_file:
            self._save_as_file()
            return

        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.code_editor.toPlainText())
            self.save_btn.setEnabled(False)
            self.save_as_btn.setEnabled(False)
            QMessageBox.information(self, "成功", "文件已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存文件: {e}")

    def _save_as_file(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存策略文件", str(Path.home()), "Python文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.code_editor.toPlainText())
                self.current_file = file_path
                self.file_label.setText(f"文件: {Path(file_path).name}")
                self.save_btn.setEnabled(False)
                self.save_as_btn.setEnabled(False)
                QMessageBox.information(self, "成功", "文件已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {e}")

    def get_strategy_file(self) -> str:
        """获取当前策略文件路径"""
        return self.current_file

    def get_strategy_content(self) -> str:
        """获取策略代码内容"""
        return self.code_editor.toPlainText()
