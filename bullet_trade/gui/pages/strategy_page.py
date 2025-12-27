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
    QListWidget,
    QListWidgetItem,
)
from PyQt6.QtGui import QFont

from ..theme import get_code_editor_style, COLORS, FONTS, SPACING, RADIUS
from ..strategy_manager import StrategyManager
from ..message_helper import show_info, show_warning, show_error, show_confirm


class StrategyPage(QWidget):
    """策略管理页面"""

    def __init__(self, auth_manager=None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.current_file = None
        self.current_remote_strategy_id = None

        # 初始化策略管理器
        self.strategy_manager = StrategyManager(auth_manager)
        self._setup_strategy_manager_callbacks()

        self._init_ui()

    def _setup_strategy_manager_callbacks(self):
        """设置策略管理器的回调函数"""
        self.strategy_manager.set_ui_callbacks(
            on_status_update=self._on_strategy_status_update,
            on_progress_message=self._on_strategy_progress_message,
            on_error=self._on_strategy_error,
            on_success=self._on_strategy_success,
            on_strategy_list_updated=self._on_strategy_list_updated,
        )

    def _on_strategy_status_update(self, status: str, message: str):
        """策略状态更新回调"""
        self._safe_ui_update(
            lambda: (
                self.download_status_label.setText(f"状态: {status}"),
                self.download_info.clear() if message else None,
                self.download_info.append(message) if message else None,
            )
        )

    def _on_strategy_progress_message(self, message: str):
        """策略进度消息回调"""
        self._safe_ui_update(lambda: self.download_info.append(message))

    def _on_strategy_error(self, title: str, message: str):
        """策略错误回调"""
        show_warning(self, message, title=title)

    def _on_strategy_success(self, title: str, message: str):
        """策略成功回调"""
        show_info(self, message, title=title)

    def _on_strategy_list_updated(self, strategies):
        """策略列表更新回调"""
        self._safe_ui_update(
            lambda: (
                self.remote_list.clear(),
                self.remote_meta.clear(),
            )
        )

        for strategy in strategies:
            # strategy 是 StrategyListItem 对象
            item = QListWidgetItem(f"{strategy.id}  {strategy.name}")
            item.setData(256, strategy.meta or "")  # Qt.UserRole = 256
            self._safe_ui_update(lambda: self.remote_list.addItem(item))

    def _safe_ui_update(self, update_func):
        """安全地更新UI，避免对象已被删除的错误"""
        try:
            update_func()
        except RuntimeError:
            # UI对象已被删除，静默退出
            pass

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

        # 远端策略管理区域（直接从服务器动态获取和解密策略）
        remote_group = QGroupBox("远端可访问策略")
        remote_layout = QVBoxLayout(remote_group)

        remote_toolbar = QHBoxLayout()
        self.remote_refresh_btn = QPushButton("刷新远端列表")
        self.remote_refresh_btn.clicked.connect(self._refresh_remote_list)
        remote_toolbar.addWidget(self.remote_refresh_btn)
        remote_toolbar.addStretch()

        # 策略下载按钮
        self.remote_download_btn = QPushButton("下载策略")
        self.remote_download_btn.setEnabled(False)
        self.remote_download_btn.clicked.connect(self._download_remote_strategy)
        remote_toolbar.addWidget(self.remote_download_btn)

        remote_layout.addLayout(remote_toolbar)

        self.remote_list = QListWidget()
        self.remote_list.itemSelectionChanged.connect(self._on_remote_selected)
        # 设置列表样式，确保文字可见
        self.remote_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_medium']};
                border-radius: {RADIUS['md']};
                padding: 4px;
            }}
            QListWidget::item {{
                color: {COLORS['text_primary']};
                padding: 8px;
                border-radius: {RADIUS['sm']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_white']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['primary_hover']};
                color: {COLORS['text_white']};
            }}
            """
        )
        remote_layout.addWidget(self.remote_list)

        self.remote_meta = QTextEdit()
        self.remote_meta.setReadOnly(True)
        self.remote_meta.setPlaceholderText("选择远端策略以查看元信息")
        remote_layout.addWidget(self.remote_meta)

        # 策略下载状态区域
        download_group = QGroupBox("策略下载状态")
        download_layout = QVBoxLayout(download_group)

        download_toolbar = QHBoxLayout()
        self.download_status_label = QLabel("状态: 未下载")
        download_toolbar.addWidget(self.download_status_label)

        download_toolbar.addStretch()
        self.download_clear_btn = QPushButton("清除缓存")
        self.download_clear_btn.clicked.connect(self._clear_download_cache)
        download_toolbar.addWidget(self.download_clear_btn)

        download_layout.addLayout(download_toolbar)

        self.download_info = QTextEdit()
        self.download_info.setReadOnly(True)
        self.download_info.setPlaceholderText("策略下载状态信息将显示在这里。\n注意：远端策略代码是加密的，下载后不会在本地显示。")
        self.download_info.setMaximumHeight(150)
        download_layout.addWidget(self.download_info)

        layout.addWidget(remote_group)

        # 提示信息
        info_label = QLabel(
            "提示：策略文件应包含 initialize(context) 函数，"
            "可选包含 handle_data(context, data)、before_trading_start(context) 等函数\n\n"
            "注意：远端策略是加密保护的，下载后不会在本地显示代码内容。"
            "下载的策略可以直接用于回测和实盘交易，但不能在本地编辑或查看。"
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
            self,
            "选择策略文件",
            str(Path.home()),
            "Python文件 (*.py);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            self.load_strategy_file(file_path)

    def _refresh_remote_list(self):
        """从后端刷新可访问策略列表（只显示元信息）"""
        self.strategy_manager.refresh_remote_list()

    def _on_remote_selected(self):
        it = self.remote_list.currentItem()
        if not it:
            self.remote_meta.clear()
            self.current_remote_strategy_id = None
            return

        # 解析策略ID
        text = it.text()
        sid = text.split()[0] if text else ""
        self.current_remote_strategy_id = sid

        meta = it.data(256) or ""
        # meta may be JSON string; pretty-print if possible
        try:
            import json as _json

            parsed = _json.loads(meta) if isinstance(meta, str) and meta else None
            if parsed:
                pretty = _json.dumps(parsed, ensure_ascii=False, indent=2)
            else:
                pretty = str(meta)
        except Exception:
            pretty = str(meta)
        self.remote_meta.setPlainText(pretty)

        # 启用下载按钮
        self.remote_download_btn.setEnabled(True)

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
            show_error(self, f"无法打开文件: {e}", title="错误")

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
            show_info(self, "文件已保存", title="成功")
        except Exception as e:
            show_error(self, f"无法保存文件: {e}", title="错误")

    def _save_as_file(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存策略文件",
            str(Path.home()),
            "Python文件 (*.py);;所有文件 (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.code_editor.toPlainText())
                self.current_file = file_path
                self.file_label.setText(f"文件: {Path(file_path).name}")
                self.save_btn.setEnabled(False)
                self.save_as_btn.setEnabled(False)
                show_info(self, "文件已保存", title="成功")
            except Exception as e:
                show_error(self, f"无法保存文件: {e}", title="错误")

    def get_strategy_file(self) -> str:
        """获取当前策略文件路径"""
        return self.current_file

    def get_strategy_content(self) -> str:
        """获取策略代码内容"""
        return self.code_editor.toPlainText()

    def _download_remote_strategy(self):
        """下载并解密远程策略"""
        if not self.current_remote_strategy_id:
            show_warning(self, "请先选择要下载的远端策略")
            return

        self.strategy_manager.download_strategy(self.current_remote_strategy_id)

    def _clear_download_cache(self):
        """清除下载缓存"""
        self.strategy_manager.clear_download_cache()
        self._safe_ui_update(lambda: (self.download_info.clear(),))
        show_info(self, "下载缓存已清除", title="成功")
