"""
策略参数配置组件
"""

from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QLabel,
    QGroupBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt

from ...utils.strategy_params import extract_strategy_params


class StrategyParamsWidget(QWidget):
    """策略参数配置组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.params_config = {}  # 参数配置信息
        self.param_widgets = {}  # 参数控件字典
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(250)  # 设置最小高度
        # 确保滚动区域与面板背景为白色
        scroll.setStyleSheet(
            """
            QScrollArea {
                background-color: #FFFFFF;
                border: none;
            }
            QScrollArea QWidget {
                background-color: #FFFFFF;
            }
        """
        )

        # 参数组
        self.params_group = QGroupBox("策略参数")
        self.params_group.setMinimumHeight(200)  # 设置参数组最小高度
        # 设置面板背景为白色
        self.params_group.setStyleSheet(
            """
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
                padding-bottom: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                color: #1A1A1A;
            }
        """
        )
        self.params_layout = QFormLayout(self.params_group)
        self.params_layout.setSpacing(8)
        self.params_layout.setVerticalSpacing(8)

        # 提示标签
        self.hint_label = QLabel("请先选择策略文件以加载参数")
        self.hint_label.setStyleSheet("color: #666; font-style: italic;")
        self.params_layout.addRow(self.hint_label)

        scroll.setWidget(self.params_group)
        layout.addWidget(scroll)

    def load_strategy_params(self, strategy_file: str):
        """
        加载策略参数

        Args:
            strategy_file: 策略文件路径
        """
        # 清空现有参数
        self._clear_params()

        if not strategy_file or not Path(strategy_file).exists():
            if self.hint_label:
                self.hint_label.setText("策略文件不存在")
                self.hint_label.show()
            return

        # 提取参数
        self.params_config = extract_strategy_params(strategy_file)

        if not self.params_config:
            if self.hint_label:
                self.hint_label.setText("未找到可配置的参数（g.变量）")
                self.hint_label.show()
            return

        # 隐藏提示标签
        if self.hint_label:
            self.hint_label.hide()

        # 创建参数控件
        for param_name, param_info in self.params_config.items():
            widget = self._create_param_widget(param_name, param_info)
            if widget:
                self.param_widgets[param_name] = widget
                label_text = param_info.get("description", param_name)
                self.params_layout.addRow(f"{param_name}:", widget)

        # 如果没有参数，显示提示
        if not self.param_widgets:
            if self.hint_label:
                self.hint_label.setText("未找到可配置的参数")
                self.hint_label.show()

    def load_strategy_params_from_source(self, source: str):
        """
        从源码字符串加载策略参数（用于内存中解密的远端策略）
        """
        # 清空现有参数
        self._clear_params()

        if not source:
            if self.hint_label:
                self.hint_label.setText("策略源码为空")
                self.hint_label.show()
            return

        # 提取参数
        from ...utils.strategy_params import extract_strategy_params_from_source

        self.params_config = extract_strategy_params_from_source(source)

        if not self.params_config:
            if self.hint_label:
                self.hint_label.setText("未找到可配置的参数（g.变量）")
                self.hint_label.show()
            return

        # 隐藏提示标签
        if self.hint_label:
            self.hint_label.hide()

        # 创建参数控件（与 load_strategy_params 相同）
        for param_name, param_info in self.params_config.items():
            widget = self._create_param_widget(param_name, param_info)
            if widget:
                self.param_widgets[param_name] = widget
                label_text = param_info.get("description", param_name)
                self.params_layout.addRow(f"{param_name}:", widget)

        if not self.param_widgets:
            if self.hint_label:
                self.hint_label.setText("未找到可配置的参数")
                self.hint_label.show()

    def _create_param_widget(
        self, param_name: str, param_info: Dict[str, Any]
    ) -> Optional[QWidget]:
        """创建参数控件"""
        param_type = param_info.get("type", "str")
        default_value = param_info.get("default")

        if param_type == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(default_value) if default_value is not None else False)
            return widget
        elif param_type == "int":
            widget = QSpinBox()
            widget.setRange(-999999999, 999999999)
            widget.setValue(int(default_value) if default_value is not None else 0)
            return widget
        elif param_type == "float":
            widget = QDoubleSpinBox()
            widget.setRange(-999999999.0, 999999999.0)
            widget.setDecimals(6)
            widget.setValue(float(default_value) if default_value is not None else 0.0)
            return widget
        elif param_type == "list":
            # 列表类型，使用文本输入（逗号分隔）
            widget = QLineEdit()
            if isinstance(default_value, (list, tuple)):
                widget.setText(",".join(str(v) for v in default_value))
            elif default_value is not None:
                widget.setText(str(default_value))
            return widget
        else:
            # 字符串类型
            widget = QLineEdit()
            if default_value is not None:
                widget.setText(str(default_value))
            return widget

    def get_params(self) -> Dict[str, Any]:
        """获取当前参数值"""
        params = {}
        for param_name, widget in self.param_widgets.items():
            param_info = self.params_config.get(param_name, {})
            param_type = param_info.get("type", "str")

            if isinstance(widget, QCheckBox):
                params[param_name] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QLineEdit):
                value_str = widget.text().strip()
                if param_type == "list":
                    # 解析逗号分隔的列表
                    if value_str:
                        params[param_name] = [v.strip() for v in value_str.split(",") if v.strip()]
                    else:
                        params[param_name] = []
                else:
                    params[param_name] = value_str

        return params

    def _clear_params(self):
        """清空参数控件"""
        # 移除所有参数行（保留提示标签）
        # 从后往前删除，避免索引问题
        row_count = self.params_layout.rowCount()
        rows_to_remove = []

        for i in range(row_count - 1, -1, -1):
            # 获取该行的标签和控件
            label_item = self.params_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = self.params_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)

            # 如果这一行包含 hint_label，跳过
            if label_item:
                widget = label_item.widget()
                if widget == self.hint_label:
                    continue
            if field_item:
                widget = field_item.widget()
                if widget == self.hint_label:
                    continue

            # 标记为需要删除
            rows_to_remove.append(i)

        # 删除标记的行
        for i in rows_to_remove:
            try:
                self.params_layout.removeRow(i)
            except Exception:
                pass  # 忽略删除错误

        self.param_widgets.clear()
        self.params_config.clear()

        # 确保 hint_label 存在且可见
        if self.hint_label:
            try:
                # 检查 hint_label 是否还在布局中
                found = False
                for i in range(self.params_layout.rowCount()):
                    label_item = self.params_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                    field_item = self.params_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
                    if (label_item and label_item.widget() == self.hint_label) or (
                        field_item and field_item.widget() == self.hint_label
                    ):
                        found = True
                        break

                if not found:
                    # 如果不在布局中，重新添加
                    self.params_layout.addRow(self.hint_label)

                self.hint_label.show()
                self.hint_label.setText("请先选择策略文件以加载参数")
            except RuntimeError:
                # 如果 hint_label 已被删除，重新创建
                self.hint_label = QLabel("请先选择策略文件以加载参数")
                self.hint_label.setStyleSheet("color: #666; font-style: italic;")
                self.params_layout.addRow(self.hint_label)
