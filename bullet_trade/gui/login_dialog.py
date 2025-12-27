"""
BulletTrade 登录对话框
"""

from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer

from .theme import COLORS, FONTS, SPACING, RADIUS


class LoginThread(QThread):
    """登录线程 - 在后台执行登录验证"""

    # 信号：登录完成 (success: bool, message: str)
    login_finished = pyqtSignal(bool, str)

    def __init__(self, auth_manager, username, password):
        super().__init__()
        self.auth_manager = auth_manager
        self.username = username
        self.password = password

    def run(self):
        """在后台线程执行登录"""
        try:
            success = self.auth_manager.authenticate(self.username, self.password)
            if success:
                self.login_finished.emit(True, "登录成功")
            else:
                self.login_finished.emit(False, "用户名或密码错误")
        except Exception as e:
            self.login_finished.emit(False, f"登录失败: {str(e)}")


class LoginDialog(QDialog):
    """登录对话框"""

    # 登录成功信号
    login_success = pyqtSignal(str)  # 参数：用户名

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BulletTrade - 登录")
        self.setModal(True)
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

        # 用户认证状态
        self.auth_manager = None
        self.login_thread = None  # 登录线程
        self.loading_dots = 0  # 加载动画点数
        self.is_loading = False  # 是否正在加载

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题区域
        title_widget = QWidget()
        title_widget.setFixedHeight(120)
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(40, 20, 40, 20)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 应用名称
        title_label = QLabel("BulletTrade")
        title_label.setStyleSheet(
            f"""
            font-size: {FONTS['size_xlarge']};
            font-weight: bold;
            color: {COLORS['primary']};
            margin-top: {SPACING['sm']};
        """
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("量化交易系统")
        subtitle_label.setStyleSheet(
            f"""
            font-size: {FONTS['size_normal']};
            color: {COLORS['text_secondary']};
            margin-top: {SPACING['xs']};
        """
        )
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle_label)

        main_layout.addWidget(title_widget)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"color: {COLORS['border_light']}; margin: 0 {SPACING['lg']};")
        main_layout.addWidget(separator)

        # 登录表单区域
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(16)  # SPACING['lg'] 的像素值

        # 用户名输入
        username_layout = QVBoxLayout()
        username_layout.setSpacing(4)  # SPACING['xs'] 的像素值

        username_label = QLabel("用户名")
        username_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        username_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        username_layout.addWidget(self.username_input)

        form_layout.addLayout(username_layout)

        # 密码输入
        password_layout = QVBoxLayout()
        password_layout.setSpacing(4)  # SPACING['xs'] 的像素值

        password_label = QLabel("密码")
        password_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        password_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)

        form_layout.addLayout(password_layout)

        # 记住密码复选框和状态显示
        bottom_layout = QHBoxLayout()

        # 状态标签
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_small']};"
        )
        self._update_status_label()
        bottom_layout.addWidget(self.status_label)

        bottom_layout.addStretch()

        self.remember_checkbox = QCheckBox("记住我")
        self.remember_checkbox.setChecked(True)
        self.remember_checkbox.setStyleSheet(f"color: {COLORS['text_secondary']};")
        bottom_layout.addWidget(self.remember_checkbox)

        form_layout.addLayout(bottom_layout)

        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setProperty("class", "primary")
        self.login_button.clicked.connect(self._on_login_clicked)
        form_layout.addWidget(self.login_button)

        main_layout.addWidget(form_widget)

        # 底部信息
        footer_widget = QWidget()
        footer_widget.setFixedHeight(40)
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(40, 0, 40, 10)

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(
            f"color: {COLORS['text_tertiary']}; font-size: {FONTS['size_small']};"
        )
        footer_layout.addWidget(version_label)

        footer_layout.addStretch()

        help_label = QLabel("忘记密码？")
        help_label.setStyleSheet(
            f"""
            color: {COLORS['primary']};
            font-size: {FONTS['size_small']};
            text-decoration: underline;
        """
        )
        help_label.setCursor(Qt.CursorShape.PointingHandCursor)
        help_label.mousePressEvent = lambda e: self._show_help()
        footer_layout.addWidget(help_label)

        main_layout.addWidget(footer_widget)

        # 设置Tab顺序
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.remember_checkbox)
        self.setTabOrder(self.remember_checkbox, self.login_button)

        # 连接回车键
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.password_input.returnPressed.connect(self._on_login_clicked)

    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                border-radius: {RADIUS['lg']};
                border: 1px solid {COLORS['border_light']};
            }}

            QLineEdit {{
                border: 1px solid {COLORS['border_medium']};
                border-radius: {RADIUS['md']};
                padding: {SPACING['sm']} {SPACING['md']};
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                font-size: {FONTS['size_normal']};
                min-height: 16px;
                height: 16px;
            }}

            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
                padding: 7px 11px;
            }}

            QLineEdit::placeholder {{
                color: {COLORS['text_tertiary']};
            }}

            QPushButton {{
                border: none;
                border-radius: {RADIUS['md']};
                padding: {SPACING['sm']} {SPACING['xl']};
                font-size: {FONTS['size_normal']};
                font-weight: 500;
                min-height: 16px;
                height: 16px;
                background-color: {COLORS['primary']};
                color: {COLORS['text_white']};
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

            QCheckBox {{
                spacing: {SPACING['sm']};
                color: {COLORS['text_secondary']};
                font-size: {FONTS['size_normal']};
            }}

            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {COLORS['border_medium']};
                border-radius: {RADIUS['sm']};
                background-color: {COLORS['bg_primary']};
            }}

            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}

            QCheckBox::indicator:hover {{
                border-color: {COLORS['primary']};
            }}
        """
        )

    def set_auth_manager(self, auth_manager):
        """设置认证管理器"""
        self.auth_manager = auth_manager

        # 加载记住的登录信息
        if self.auth_manager:
            remembered = self.auth_manager.get_remembered_credentials()
            if remembered:
                self.username_input.setText(remembered.get("username", ""))
                self.password_input.setText(remembered.get("password", ""))
                self.remember_checkbox.setChecked(True)

        # 更新状态标签
        self._update_status_label()

    def _on_login_clicked(self):
        """登录按钮点击事件"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self._show_message_box("输入错误", "请输入用户名", QMessageBox.Icon.Warning)
            self.username_input.setFocus()
            return

        if not password:
            self._show_message_box("输入错误", "请输入密码", QMessageBox.Icon.Warning)
            self.password_input.setFocus()
            return

        # 如果正在登录，忽略重复点击
        if self.login_thread and self.login_thread.isRunning():
            return

        # 禁用输入和按钮
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.login_button.setEnabled(False)
        self.remember_checkbox.setEnabled(False)

        # 启动加载动画
        self.is_loading = True
        self.loading_dots = 0
        self._start_loading_animation()

        # 在后台线程执行登录
        self.login_thread = LoginThread(self.auth_manager, username, password)
        self.login_thread.login_finished.connect(self._on_login_completed)
        self.login_thread.start()

    def _start_loading_animation(self):
        """启动加载动画"""
        if not self.is_loading:
            return

        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.login_button.setText(f"登录中{dots}")
        # 继续动画
        QTimer.singleShot(500, self._start_loading_animation)

    def _on_login_completed(self, success: bool, message: str):
        """登录完成回调"""
        # 停止加载动画（通过is_loading标志防止动画继续）
        self.is_loading = False
        self.login_button.setText("登录")

        # 恢复输入和按钮
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.login_button.setEnabled(True)
        self.remember_checkbox.setEnabled(True)

        if success:
            # 保存记住的凭据
            username = self.username_input.text().strip()
            if self.remember_checkbox.isChecked() and self.auth_manager:
                self.auth_manager.save_credentials(username, self.password_input.text())
            else:
                self.auth_manager.clear_credentials()

            # 发送登录成功信号
            self.login_success.emit(username)
            self.accept()
        else:
            # 显示错误信息
            self._show_message_box(
                "登录失败",
                f"{message}\n\n请检查后端服务器是否正常运行。",
                QMessageBox.Icon.Warning,
            )
            self.password_input.clear()
            self.password_input.setFocus()

    def _update_status_label(self):
        """更新状态标签"""
        if self.auth_manager and hasattr(self.auth_manager, "check_backend_available"):
            if self.auth_manager.check_backend_available():
                self.status_label.setText("✓ 后端服务器连接正常")
                self.status_label.setStyleSheet(
                    f"color: {COLORS['success']}; font-size: {FONTS['size_small']};"
                )
            else:
                self.status_label.setText("✗ 后端服务器连接失败")
                self.status_label.setStyleSheet(
                    f"color: {COLORS['error']}; font-size: {FONTS['size_small']};"
                )
        else:
            self.status_label.setText("准备就绪")
            self.status_label.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_small']};"
            )

    def _show_message_box(self, title: str, text: str, icon=QMessageBox.Icon.Warning):
        """
        统一显示消息框并强制设置样式，避免在某些系统主题下内容不可见的问题。
        """
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        # 明确设置消息框内文字颜色，保证在深色/浅色主题下都可见
        msg.setStyleSheet(
            f"""
            QMessageBox {{
                background-color: {COLORS['bg_primary']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
            }}
            QMessageBox QPushButton {{
                color: {COLORS['text_primary']};
            }}
            """
        )
        msg.exec()

    def _show_help(self):
        """显示帮助信息"""
        self._show_message_box(
            "帮助",
            "忘记密码请联系系统管理员重置密码。\n\n" "如遇登录问题，请检查后端服务器是否正常运行。",
            QMessageBox.Icon.Information,
        )

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 聚焦到用户名输入框
        self.username_input.setFocus()

    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_Escape:
            # ESC键关闭对话框
            self.reject()
        else:
            super().keyPressEvent(event)
