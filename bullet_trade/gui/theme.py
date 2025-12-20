"""
BulletTrade GUI 主题配置
极简主义风格，蓝白配色
"""

# 颜色定义
COLORS = {
    # 主色调 - 蓝色系
    "primary": "#2196F3",  # 主蓝色
    "primary_dark": "#1976D2",  # 深蓝色
    "primary_light": "#64B5F6",  # 浅蓝色
    "primary_hover": "#42A5F5",  # 悬停蓝色
    # 背景色 - 白色系
    "bg_primary": "#FFFFFF",  # 主背景（白色）
    "bg_secondary": "#F5F7FA",  # 次背景（浅灰白）
    "bg_tertiary": "#FAFBFC",  # 三级背景（极浅灰）
    # 文字颜色
    "text_primary": "#1A1A1A",  # 主文字（深灰黑）
    "text_secondary": "#6B7280",  # 次文字（中灰）
    "text_tertiary": "#9CA3AF",  # 三级文字（浅灰）
    "text_white": "#FFFFFF",  # 白色文字
    # 边框颜色
    "border_light": "#E5E7EB",  # 浅边框
    "border_medium": "#D1D5DB",  # 中边框
    "border_dark": "#9CA3AF",  # 深边框
    # 状态颜色
    "success": "#10B981",  # 成功（绿色）
    "warning": "#F59E0B",  # 警告（橙色）
    "error": "#EF4444",  # 错误（红色）
    "info": "#3B82F6",  # 信息（蓝色）
    # 中性色
    "neutral_50": "#F9FAFB",
    "neutral_100": "#F3F4F6",
    "neutral_200": "#E5E7EB",
    "neutral_300": "#D1D5DB",
    "neutral_400": "#9CA3AF",
    "neutral_500": "#6B7280",
    "neutral_600": "#4B5563",
    "neutral_700": "#374151",
    "neutral_800": "#1F2937",
    "neutral_900": "#111827",
}

# 字体定义
FONTS = {
    "default": "Microsoft YaHei UI, Segoe UI, Arial, sans-serif",
    "monospace": "Consolas, Monaco, Courier New, monospace",
    "size_small": "9pt",
    "size_normal": "10pt",
    "size_medium": "11pt",
    "size_large": "12pt",
    "size_xlarge": "14pt",
}

# 间距定义
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
    "xxl": "32px",
}

# 圆角定义
RADIUS = {
    "none": "0px",
    "sm": "4px",
    "md": "6px",
    "lg": "8px",
    "xl": "12px",
    "full": "9999px",
}

# 阴影定义
SHADOWS = {
    "none": "none",
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "md": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
    "lg": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "xl": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
}


def get_main_stylesheet() -> str:
    """获取主窗口样式表"""
    return f"""
    /* 主窗口 */
    QMainWindow {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        font-family: {FONTS['default']};
        font-size: {FONTS['size_normal']};
    }}
    
    /* 菜单栏 */
    QMenuBar {{
        background-color: {COLORS['bg_primary']};
        border-bottom: 1px solid {COLORS['border_light']};
        padding: {SPACING['sm']} 0;
        color: {COLORS['text_primary']};
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: {SPACING['sm']} {SPACING['lg']};
        border-radius: {RADIUS['sm']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['primary']};
    }}
    
    QMenu {{
        background-color: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['sm']};
        box-shadow: {SHADOWS['lg']};
    }}
    
    QMenu::item {{
        padding: {SPACING['sm']} {SPACING['lg']};
        border-radius: {RADIUS['sm']};
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
    }}
    
    /* 标签页 */
    QTabWidget::pane {{
        border: none;
        background-color: {COLORS['bg_primary']};
        border-radius: {RADIUS['md']};
    }}
    
    QTabBar::tab {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
        padding: {SPACING['md']} {SPACING['xl']};
        margin-right: {SPACING['xs']};
        border: none;
        border-bottom: 2px solid transparent;
        font-weight: 500;
    }}
    
    QTabBar::tab:selected {{
        color: {COLORS['primary']};
        border-bottom: 2px solid {COLORS['primary']};
        background-color: transparent;
    }}
    
    QTabBar::tab:hover {{
        color: {COLORS['primary_dark']};
        background-color: {COLORS['bg_secondary']};
    }}
    
    /* 状态栏 */
    QStatusBar {{
        background-color: {COLORS['bg_primary']};
        border-top: 1px solid {COLORS['border_light']};
        color: {COLORS['text_secondary']};
        padding: {SPACING['sm']};
    }}
    
    /* 按钮 */
    QPushButton {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_medium']};
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['lg']};
        font-weight: 500;
        min-height: 28px;
        height: 28px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['bg_secondary']};
        border-color: {COLORS['primary']};
        color: {COLORS['primary']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        border-color: {COLORS['primary']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_tertiary']};
        border-color: {COLORS['border_light']};
    }}
    
    /* 主要按钮 */
    QPushButton[class="primary"] {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        border: none;
    }}
    
    QPushButton[class="primary"]:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    
    QPushButton[class="primary"]:pressed {{
        background-color: {COLORS['primary_dark']};
    }}
    
    /* 输入框 */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_medium']};
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['md']};
        min-height: 28px;
        height: 28px;
        selection-background-color: {COLORS['primary_light']};
        selection-color: {COLORS['text_white']};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {COLORS['primary']};
        padding: 4px 11px;
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_tertiary']};
        border-color: {COLORS['border_light']};
    }}
    
    /* 组合框 */
    QComboBox {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_medium']};
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['md']};
        min-height: 28px;
        height: 28px;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS['primary']};
    }}
    
    QComboBox:focus {{
        border: 2px solid {COLORS['primary']};
        padding: 4px 11px;
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
        width: 0;
        height: 0;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        selection-background-color: {COLORS['primary']};
        selection-color: {COLORS['text_white']};
        padding: 4px;
        outline: none;
    }}
    
    QComboBox QAbstractItemView::item {{
        color: {COLORS['text_primary']};
        padding: 8px {SPACING['md']};
        min-height: 32px;
        border-radius: {RADIUS['sm']};
        background-color: transparent;
    }}
    
    QComboBox QAbstractItemView::item:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
    }}
    
    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS['primary_light']};
        color: {COLORS['text_white']};
    }}
    
    /* 日期选择器 */
    QDateEdit {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_medium']};
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['md']};
        min-height: 28px;
        height: 28px;
    }}
    
    QDateEdit:focus {{
        border: 2px solid {COLORS['primary']};
        padding: 4px 11px;
    }}
    
    /* 数字输入框 */
    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_medium']};
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['md']};
        min-height: 28px;
        height: 28px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLORS['primary']};
        padding: 4px 11px;
    }}
    
    /* 分组框 */
    QGroupBox {{
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        margin-top: {SPACING['md']};
        padding-top: {SPACING['lg']};
        padding-bottom: {SPACING['md']};
        background-color: {COLORS['bg_primary']};
        font-weight: 500;
        color: {COLORS['text_primary']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: {SPACING['md']};
        padding: 0 {SPACING['sm']};
        color: {COLORS['text_primary']};
    }}
    
    /* 表单布局 */
    QFormLayout {{
        spacing: {SPACING['md']};
    }}
    
    QFormLayout > QLabel {{
        min-width: 100px;
        color: {COLORS['text_primary']};
    }}
    
    /* 标签 */
    QLabel {{
        color: {COLORS['text_primary']};
    }}
    
    /* 进度条 */
    QProgressBar {{
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        background-color: {COLORS['bg_secondary']};
        text-align: center;
        height: 24px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['primary']};
        border-radius: {RADIUS['sm']};
    }}
    
    /* 滚动条 */
    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border_medium']};
        border-radius: {RADIUS['sm']};
        min-height: 30px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        background-color: {COLORS['bg_secondary']};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {COLORS['border_medium']};
        border-radius: {RADIUS['sm']};
        min-width: 30px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    
    /* 消息框（弹窗） */
    QMessageBox {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: {FONTS['default']};
        font-size: {FONTS['size_normal']};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        min-width: 300px;
        padding: {SPACING['md']};
    }}
    
    QMessageBox QPushButton {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_medium']};
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['xl']};
        min-width: 80px;
        min-height: 28px;
        height: 28px;
        font-weight: 500;
    }}
    
    QMessageBox QPushButton:hover {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        border-color: {COLORS['primary']};
    }}
    
    QMessageBox QPushButton:pressed {{
        background-color: {COLORS['primary_dark']};
        color: {COLORS['text_white']};
        border-color: {COLORS['primary_dark']};
    }}
    
    QMessageBox QPushButton:default {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        border: none;
    }}
    
    QMessageBox QPushButton:default:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    
    QMessageBox QPushButton:default:pressed {{
        background-color: {COLORS['primary_dark']};
    }}
    """


def get_button_primary_style() -> str:
    """获取主要按钮样式"""
    return f"""
    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        border: none;
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['lg']};
        font-weight: 500;
        min-height: 28px;
        height: 28px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['primary_dark']};
    }}
    QPushButton:disabled {{
        background-color: {COLORS['neutral_300']};
        color: {COLORS['text_tertiary']};
    }}
    """


def get_button_danger_style() -> str:
    """获取危险按钮样式（如停止、删除）"""
    return f"""
    QPushButton {{
        background-color: {COLORS['error']};
        color: {COLORS['text_white']};
        border: none;
        border-radius: {RADIUS['md']};
        padding: 5px {SPACING['lg']};
        font-weight: 500;
        min-height: 28px;
        height: 28px;
    }}
    QPushButton:hover {{
        background-color: #DC2626;
    }}
    QPushButton:pressed {{
        background-color: #B91C1C;
    }}
    QPushButton:disabled {{
        background-color: {COLORS['neutral_300']};
        color: {COLORS['text_tertiary']};
    }}
    """


def get_code_editor_style() -> str:
    """获取代码编辑器样式"""
    return f"""
    QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['md']};
        font-family: {FONTS['monospace']};
        font-size: {FONTS['size_normal']};
        selection-background-color: {COLORS['primary_light']};
        selection-color: {COLORS['text_white']};
    }}
    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {COLORS['primary']};
        padding: 11px;
    }}
    """


def get_log_text_style() -> str:
    """获取日志文本样式"""
    return f"""
    QTextEdit {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        padding: {SPACING['md']};
        font-family: {FONTS['monospace']};
        font-size: {FONTS['size_small']};
    }}
    """
