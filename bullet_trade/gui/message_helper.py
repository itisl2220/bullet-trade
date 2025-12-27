"""
弹窗辅助工具 - 统一管理所有弹窗的显示
提供美化的样式、中文按钮、自动调整窗口大小
"""

from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import Qt
from .theme import COLORS


class MessageHelper:
    """弹窗辅助类"""

    @staticmethod
    def _apply_style(msg_box: QMessageBox, msg_type: str = "info"):
        """应用弹窗样式并设置中文按钮"""
        # 设置窗口属性
        msg_box.setWindowTitle("提示")

        # 应用样式
        msg_box.setStyleSheet(
            f"""
            QMessageBox {{
                background-color: {COLORS['bg_primary']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
                min-width: 350px;
                min-height: 60px;
                padding: 12px;
            }}
            QMessageBox QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_white']};
                border: none;
                border-radius: 6px;
                padding: 6px 24px;
                min-width: 90px;
                min-height: 28px;
                font-weight: 500;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {COLORS['primary_dark']};
            }}
        """
        )

        # 调整窗口大小以适应内容
        msg_box.setFixedWidth(500)
        msg_box.setFixedHeight(200)

        return msg_box

    @staticmethod
    def info(parent: QWidget, title: str, message: str) -> None:
        """信息提示框"""
        msg_box = QMessageBox(parent)
        msg_box.setText(message)
        MessageHelper._apply_style(msg_box, "info")

        # 清除默认按钮，添加中文按钮
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.button(QMessageBox.StandardButton.Ok).setText("确定")

        msg_box.exec()

    @staticmethod
    def success(parent: QWidget, title: str, message: str) -> None:
        """成功提示框"""
        msg_box = QMessageBox(parent)
        msg_box.setText(message)
        MessageHelper._apply_style(msg_box, "success")

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.button(QMessageBox.StandardButton.Ok).setText("确定")

        msg_box.exec()

    @staticmethod
    def warning(parent: QWidget, title: str, message: str) -> None:
        """警告提示框"""
        msg_box = QMessageBox(parent)
        msg_box.setText(message)
        MessageHelper._apply_style(msg_box, "warning")

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.button(QMessageBox.StandardButton.Ok).setText("确定")

        msg_box.exec()

    @staticmethod
    def error(parent: QWidget, title: str, message: str) -> None:
        """错误提示框"""
        msg_box = QMessageBox(parent)
        msg_box.setText(message)
        MessageHelper._apply_style(msg_box, "error")

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.button(QMessageBox.StandardButton.Ok).setText("确定")

        msg_box.exec()

    @staticmethod
    def confirm(parent: QWidget, title: str, message: str, default_ok: bool = False) -> bool:
        """
        确认对话框

        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
            default_ok: 默认按钮是否为"确定"（True为确定，False为取消）

        Returns:
            bool: 用户点击确定返回True，点击取消返回False
        """
        msg_box = QMessageBox(parent)
        msg_box.setText(message)
        MessageHelper._apply_style(msg_box, "question")

        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        ok_button = msg_box.button(QMessageBox.StandardButton.Yes)
        cancel_button = msg_box.button(QMessageBox.StandardButton.No)

        ok_button.setText("确定")
        cancel_button.setText("取消")

        # 设置默认按钮
        if default_ok:
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        else:
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes

    @staticmethod
    def confirm_delete(parent: QWidget, item_name: str = "") -> bool:
        """
        删除确认对话框（专用）

        Args:
            item_name: 要删除的项目名称

        Returns:
            bool: 用户确认删除返回True，否则返回False
        """
        message = (
            f"确定要删除{item_name}吗？\\n\\n此操作无法撤销！"
            if item_name
            else "确定要删除吗？\\n\\n此操作无法撤销！"
        )
        return MessageHelper.confirm(parent, "确认删除", message, default_ok=False)

    @staticmethod
    def confirm_save(parent: QWidget, item_name: str = "") -> bool:
        """
        保存确认对话框（专用）

        Args:
            item_name: 要保存的项目名称

        Returns:
            bool: 用户确认保存返回True，否则返回False
        """
        message = f"是否保存{item_name}？" if item_name else "是否保存？"
        return MessageHelper.confirm(parent, "确认保存", message, default_ok=True)

    @staticmethod
    def question(parent: QWidget, title: str, message: str, buttons: list = None) -> int:
        """
        通用询问对话框

        Args:
            parent: 父窗口
            title: 标题
            message: 消息内容
            buttons: 按钮文字列表，如 ["是", "否", "取消"]

        Returns:
            int: 用户点击的按钮索引（0-based）
        """
        msg_box = QMessageBox(parent)
        msg_box.setText(message)
        MessageHelper._apply_style(msg_box, "question")

        if buttons is None:
            buttons = ["是", "否"]

        # 根据按钮数量设置标准按钮
        if len(buttons) == 2:
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.button(QMessageBox.StandardButton.Yes).setText(buttons[0])
            msg_box.button(QMessageBox.StandardButton.No).setText(buttons[1])
        elif len(buttons) == 3:
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel
            )
            msg_box.button(QMessageBox.StandardButton.Yes).setText(buttons[0])
            msg_box.button(QMessageBox.StandardButton.No).setText(buttons[1])
            msg_box.button(QMessageBox.StandardButton.Cancel).setText(buttons[2])
        else:
            # 单按钮
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.button(QMessageBox.StandardButton.Ok).setText(buttons[0])

        result = msg_box.exec()

        # 返回按钮索引
        if result == QMessageBox.StandardButton.Yes:
            return 0
        elif result == QMessageBox.StandardButton.No:
            return 1
        elif result == QMessageBox.StandardButton.Cancel:
            return 2
        else:
            return 0


# 便捷函数
def show_info(parent: QWidget, message: str, title: str = "提示") -> None:
    """显示信息提示"""
    MessageHelper.info(parent, title, message)


def show_success(parent: QWidget, message: str, title: str = "成功") -> None:
    """显示成功提示"""
    MessageHelper.success(parent, title, message)


def show_warning(parent: QWidget, message: str, title: str = "警告") -> None:
    """显示警告提示"""
    MessageHelper.warning(parent, title, message)


def show_error(parent: QWidget, message: str, title: str = "错误") -> None:
    """显示错误提示"""
    MessageHelper.error(parent, title, message)


def show_confirm(
    parent: QWidget, message: str, title: str = "确认", default_ok: bool = False
) -> bool:
    """显示确认对话框"""
    return MessageHelper.confirm(parent, title, message, default_ok)
