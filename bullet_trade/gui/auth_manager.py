"""
BulletTrade 用户认证管理器
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from .api_client import APIClient, APIConfig


class AuthManager:
    """用户认证管理器"""

    def __init__(self, config_dir: Optional[Path] = None, api_config: Optional[APIConfig] = None):
        """
        初始化认证管理器

        Args:
            config_dir: 配置目录，默认为 ~/.bullet-trade/auth
            api_config: API配置，如果为None则从环境变量读取
        """
        if config_dir is None:
            home_dir = Path.home()
            config_dir = home_dir / ".bullet-trade" / "auth"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 配置文件路径
        self.session_file = self.config_dir / "session.json"
        self.credentials_file = self.config_dir / "credentials.json"

        # API配置
        self.api_config = api_config or APIConfig.from_env()
        self.api_client = APIClient(self.api_config.base_url)

        # 当前登录用户
        self.current_user: Optional[Dict[str, Any]] = None
        self.session_token: Optional[str] = None

        # 加载会话
        self._load_session()

    def _load_session(self):
        """加载会话信息"""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)

                # 检查会话是否过期（24小时）
                if self._is_session_valid(session_data):
                    self.current_user = session_data.get("username")
                    self.session_token = session_data.get("token")
                else:
                    # 会话过期，清除
                    self._clear_session()
            except Exception:
                self._clear_session()

    def _save_session(self, username: str, token: str):
        """保存会话信息"""
        session_data = {
            "username": username,
            "token": token,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _clear_session(self):
        """清除会话信息"""
        self.current_user = None
        self.session_token = None
        if self.session_file.exists():
            try:
                self.session_file.unlink()
            except Exception:
                pass

    def _is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """检查会话是否有效"""
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            return datetime.now() < expires_at
        except Exception:
            return False

    def _hash_password(self, password: str) -> str:
        """对密码进行哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """
        用户认证

        Args:
            username: 用户名
            password: 密码

        Returns:
            认证是否成功
        """
        try:
            # 尝试后端认证
            success, data = self.api_client.login(username, password)

            if success and isinstance(data, dict):
                # 登录成功，保存用户信息和token
                self.current_user = data.get("user", {})
                self.session_token = data.get("token")

                if self.session_token:
                    # 设置API客户端的认证token
                    self.api_client.set_auth_token(self.session_token)

                # 保存会话信息
                self._save_session(username, self.session_token or "")
                return True
            else:
                # 后端登录失败
                return False

        except Exception as e:
            print(f"认证失败: {e}")
            return False

    def _generate_token(self) -> str:
        """生成会话令牌"""
        import secrets

        return secrets.token_hex(32)

    def logout(self):
        """用户登出"""
        self._clear_session()

    def is_authenticated(self) -> bool:
        """检查当前是否已认证"""
        return self.current_user is not None and self.session_token is not None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """获取当前登录用户信息"""
        return self.current_user

    def get_current_username(self) -> Optional[str]:
        """获取当前登录用户名"""
        if self.current_user and isinstance(self.current_user, dict):
            return self.current_user.get("username")
        return None

    def get_user_info(self, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        # 如果指定了用户名且不是当前用户，暂时不支持
        if username and username != self.get_current_username():
            return None

        # 如果有缓存的用户信息，直接返回
        if self.current_user:
            return self.current_user

        # 尝试从API获取
        if self.session_token:
            success, data = self.api_client.get_current_user(self.session_token)
            if success and isinstance(data, dict):
                self.current_user = data
                return data

        return None

    def save_credentials(self, username: str, password: str):
        """保存记住的登录凭据"""
        credentials = {
            "username": username,
            "password": password,  # 注意：实际应用中应该加密存储
            "saved_at": datetime.now().isoformat(),
        }

        try:
            with open(self.credentials_file, "w", encoding="utf-8") as f:
                json.dump(credentials, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_remembered_credentials(self) -> Optional[Dict[str, str]]:
        """获取记住的登录凭据"""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    credentials = json.load(f)
                return {
                    "username": credentials.get("username", ""),
                    "password": credentials.get("password", ""),
                }
            except Exception:
                pass
        return None

    def clear_credentials(self):
        """清除记住的登录凭据"""
        if self.credentials_file.exists():
            try:
                self.credentials_file.unlink()
            except Exception:
                pass

    def change_password(self, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        修改密码

        Args:
            old_password: 旧密码
            new_password: 新密码

        Returns:
            (success: bool, message: str)
            - success: 修改是否成功
            - message: 成功消息或错误信息
        """
        if not self.session_token:
            return False, "用户未登录"

        try:
            success, data = self.api_client.change_password(
                old_password, new_password, self.session_token
            )

            if success:
                return True, data.get("message", "密码修改成功")
            else:
                return False, data if isinstance(data, str) else "密码修改失败"

        except Exception as e:
            return False, f"修改密码失败: {str(e)}"

    def check_backend_available(self) -> bool:
        """
        检查后端服务器是否可用

        Returns:
            后端是否可用
        """
        try:
            success, _ = self.api_client.health_check()
            return success
        except Exception:
            return False

    def close(self):
        """关闭认证管理器，清理资源"""
        if hasattr(self, "api_client"):
            self.api_client.close()
