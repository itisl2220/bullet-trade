"""
配置页面
表单式编辑配置，使用本地缓存
"""

from pathlib import Path
from typing import Dict, Optional, Any
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
    QScrollArea,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt

from ..theme import COLORS
from ..config_manager import ConfigManager
from ..message_helper import show_info, show_warning, show_error, show_confirm


class ConfigPage(QWidget):
    """配置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.input_widgets: Dict[str, QWidget] = {}
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存配置")
        save_btn.setStyleSheet(f"""
            background-color: {COLORS['primary']};
            color: {COLORS['text_white']};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
        """)
        save_btn.clicked.connect(self._save_config)
        toolbar_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("重置为默认")
        reset_btn.clicked.connect(self._reset_config)
        toolbar_layout.addWidget(reset_btn)
        
        apply_btn = QPushButton("应用到环境变量")
        apply_btn.setStyleSheet(f"""
            background-color: {COLORS['success']};
            color: {COLORS['text_white']};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
        """)
        apply_btn.clicked.connect(self._apply_to_env)
        toolbar_layout.addWidget(apply_btn)
        
        toolbar_layout.addStretch()
        
        main_layout.addLayout(toolbar_layout)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_primary']};
                border: none;
            }}
        """)
        
        # 配置内容容器
        config_widget = QWidget()
        config_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        """)
        self.config_layout = QVBoxLayout(config_widget)
        self.config_layout.setSpacing(15)
        self.config_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(config_widget)
        main_layout.addWidget(scroll)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            padding: 8px;
        """)
        main_layout.addWidget(self.status_label)
    
    def _load_config(self):
        """加载配置并创建UI"""
        config = self.config_manager.get_all()
        
        # 定义配置项分组（label使用中文）
        config_groups = {
            "实盘模式": [
                ('live_mode', '实盘模式', '下拉框', ['dry_run', 'live']),
            ],
            "数据源配置": [
                ('data_provider', '默认数据源', '下拉框', ['jqdata', 'qmt', 'tushare']),
                ('data_cache_dir', '数据缓存目录', '路径'),
                ('qmt_host', 'QMT主机地址', '文本'),
                ('qmt_port', 'QMT端口', '整数'),
                ('jqdata_username', '聚宽用户名', '文本'),
                ('jqdata_password', '聚宽密码', '密码'),
            ],
            "券商配置": [
                ('broker', '默认券商', '下拉框', ['simulator', 'qmt', 'qmt-remote']),
                ('qmt_account_id', 'QMT账户ID', '文本'),
                ('qmt_account_type', 'QMT账户类型', '下拉框', ['stock', 'future']),
                ('qmt_data_path', 'QMT数据路径', '路径'),
                ('qmt_server_host', 'QMT服务器主机', '文本'),
                ('qmt_server_port', 'QMT服务器端口', '整数'),
                ('qmt_server_token', 'QMT服务器Token', '密码'),
                ('simulator_initial_cash', '模拟器初始资金', '整数'),
            ],
            "风控配置": [
                ('max_order_value', '单笔订单最大金额', '整数'),
                ('max_daily_trade_value', '单日最大交易金额', '整数'),
                ('max_daily_trades', '单日最大交易次数', '整数'),
                ('max_stock_count', '最大持仓股票数', '整数'),
                ('max_position_ratio', '单只股票最大仓位(%)', '浮点数'),
                ('stop_loss_ratio', '止损比例(%)', '浮点数'),
            ],
            "系统配置": [
                ('log_dir', '日志目录', '路径'),
                ('log_level', '日志级别', '下拉框', ['DEBUG', 'INFO', 'WARNING', 'ERROR']),
                ('runtime_dir', '运行时目录', '路径'),
                ('debug', '调试模式', '布尔'),
            ],
        }
        
        # 创建分组
        for group_name, items in config_groups.items():
            group = QGroupBox(group_name)
            form_layout = QFormLayout(group)
            form_layout.setSpacing(12)
            form_layout.setVerticalSpacing(12)
            
            for item in items:
                if len(item) == 4:
                    key, label, widget_type, options = item
                else:
                    key, label, widget_type = item
                    options = None
                
                value = config.get(key, '')
                widget = self._create_input_widget(key, value, widget_type, options)
                self.input_widgets[key] = widget
                form_layout.addRow(f"{label}:", widget)
            
            self.config_layout.addWidget(group)
        
        self.config_layout.addStretch()
        
        self.status_label.setText("配置已加载")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['success']};
            padding: 8px;
        """)
    
    def _create_input_widget(self, key: str, value: Any, widget_type: str, options: Optional[list] = None) -> QWidget:
        """创建输入控件"""
        if widget_type == '下拉框':
            widget = QComboBox()
            if options:
                widget.addItems(options)
            if value:
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentIndex(0)
        elif widget_type == '布尔':
            widget = QCheckBox()
            widget.setChecked(bool(value) if value is not None else False)
        elif widget_type == '整数':
            widget = QSpinBox()
            widget.setRange(0, 999999999)
            try:
                widget.setValue(int(value) if value and str(value).strip() else 0)
            except (ValueError, TypeError):
                widget.setValue(0)
        elif widget_type == '浮点数':
            widget = QDoubleSpinBox()
            widget.setRange(0.0, 100.0)
            widget.setDecimals(2)
            widget.setSuffix('%')
            try:
                widget.setValue(float(value) if value and str(value).strip() else 0.0)
            except (ValueError, TypeError):
                widget.setValue(0.0)
        elif widget_type == '密码':
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            widget.setText(str(value) if value else '')
        elif widget_type == '路径':
            widget = QLineEdit()
            widget.setText(str(value) if value else '')
            widget.setObjectName(key)  # 设置key作为标识
            # 添加浏览按钮
            browse_btn = QPushButton("浏览...")
            browse_btn.clicked.connect(lambda checked, w=widget, k=key: self._browse_path(w, k))
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(widget)
            layout.addWidget(browse_btn)
            container = QWidget()
            container.setLayout(layout)
            return container
        else:  # 文本
            widget = QLineEdit()
            widget.setText(str(value) if value else '')
        
        return widget
    
    def _browse_path(self, line_edit: QLineEdit, key: str):
        """浏览路径"""
        current_path = line_edit.text() or str(Path.cwd())
        if 'dir' in key.lower():
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择目录", current_path, options=QFileDialog.Option.DontUseNativeDialog
            )
            if dir_path:
                line_edit.setText(dir_path)
        elif 'path' in key.lower():
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择路径", current_path, options=QFileDialog.Option.DontUseNativeDialog
            )
            if dir_path:
                line_edit.setText(dir_path)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择文件",
                current_path,
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if file_path:
                line_edit.setText(file_path)
    
    def _save_config(self):
        """保存配置"""
        try:
            # 收集所有配置值
            config = {}
            for key, widget in self.input_widgets.items():
                if isinstance(widget, QComboBox):
                    config[key] = widget.currentText()
                elif isinstance(widget, QCheckBox):
                    config[key] = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    config[key] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    config[key] = widget.value()
                elif isinstance(widget, QLineEdit):
                    config[key] = widget.text()
                elif isinstance(widget, QWidget):
                    # 处理带浏览按钮的容器
                    line_edit = widget.findChild(QLineEdit)
                    if line_edit:
                        config[key] = line_edit.text()
            
            # 保存到配置管理器
            self.config_manager.update(config)
            if self.config_manager.save():
                self.status_label.setText("配置已保存")
                self.status_label.setStyleSheet(f"""
                    color: {COLORS['success']};
                    padding: 8px;
                """)
                show_info(self, "配置已保存到本地缓存！", title="成功")
            else:
                raise Exception("保存文件失败")

        except Exception as e:
            show_error(self, f"保存配置失败:\n{str(e)}", title="错误")
            self.status_label.setText(f"保存失败: {str(e)}")
            self.status_label.setStyleSheet(f"""
                color: {COLORS['error']};
                padding: 8px;
            """)
    
    def _reset_config(self):
        """重置为默认配置"""
        if show_confirm(
            self,
            "确定要重置所有配置为默认值吗？",
            title="确认重置",
            default_ok=False,
        ):
            # 重新初始化配置管理器
            self.config_manager._init_defaults()
            self.config_manager.save()

            # 清空现有UI
            while self.config_layout.count():
                item = self.config_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.input_widgets.clear()

            # 重新加载
            self._load_config()

            show_info(self, "配置已重置为默认值！", title="成功")
    
    def _apply_to_env(self):
        """将配置应用到环境变量"""
        # 先保存配置
        self._save_config()
        
        # 应用到环境变量
        self.config_manager.apply_to_env()
        
        self.status_label.setText("配置已应用到环境变量")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['success']};
            padding: 8px;
        """)

        show_info(
            self,
            "配置已应用到环境变量！\n\n"
            "注意：这些环境变量仅在当前会话中有效。\n"
            "如需永久生效，请确保在启动时调用 apply_to_env()。",
            title="成功",
        )
    
    def get_config_manager(self) -> ConfigManager:
        """获取配置管理器实例"""
        return self.config_manager
