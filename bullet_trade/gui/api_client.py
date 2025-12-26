"""
BulletTrade API 客户端

处理与后端服务器的HTTP通信
"""

import json
import logging
from typing import Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_LOGGER = logging.getLogger(__name__)


class APIClient:
    """API客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化API客户端

        Args:
            base_url: API服务器基础URL，如 "http://localhost:3000/api"
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()

        # 配置重试策略
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
        )

        # 挂载适配器
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点（不包含base_url）
            **kwargs: 传递给requests的参数

        Returns:
            (success: bool, data: Any)
            - success: 请求是否成功
            - data: 成功时返回响应数据，失败时返回错误信息
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # 设置默认超时
        kwargs.setdefault("timeout", self.timeout)

        try:
            _LOGGER.debug(f"Making {method} request to {url}")
            response = self._session.request(method, url, **kwargs)
            _LOGGER.debug(f"Response: {response.text}")

            # 检查响应状态
            if response.status_code == 200:
                try:
                    return True, response.json()
                except json.JSONDecodeError:
                    return True, response.text
            else:
                # 尝试解析错误响应
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                except json.JSONDecodeError:
                    error_msg = response.text or f"HTTP {response.status_code}"

                _LOGGER.error(f"API request failed: {error_msg}")
                return False, error_msg

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            _LOGGER.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            _LOGGER.error(error_msg)
            return False, error_msg

    def login(self, username: str, password: str) -> Tuple[bool, Any]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            (success: bool, data: Any)
            - success: 登录是否成功
            - data: 成功时返回用户信息和token，失败时返回错误信息
        """
        payload = {"username": username, "password": password}

        return self._make_request("POST", "/auth/login", json=payload)

    def logout(self) -> Tuple[bool, Any]:
        """
        用户登出

        Returns:
            (success: bool, data: Any)
            - success: 登出是否成功
            - data: 响应数据或错误信息
        """
        return self._make_request("POST", "/auth/logout")

    def get_current_user(self, token: Optional[str] = None) -> Tuple[bool, Any]:
        """
        获取当前用户信息

        Args:
            token: JWT token（如果不提供，使用session中的token）

        Returns:
            (success: bool, data: Any)
            - success: 获取是否成功
            - data: 成功时返回用户信息，失败时返回错误信息
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return self._make_request("GET", "/auth/me", headers=headers)

    def change_password(
        self, old_password: str, new_password: str, token: Optional[str] = None
    ) -> Tuple[bool, Any]:
        """
        修改密码

        Args:
            old_password: 旧密码
            new_password: 新密码
            token: JWT token

        Returns:
            (success: bool, data: Any)
            - success: 修改是否成功
            - data: 响应数据或错误信息
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {"old_password": old_password, "new_password": new_password}

        return self._make_request("POST", "/auth/change-password", json=payload, headers=headers)

    def health_check(self) -> Tuple[bool, Any]:
        """
        健康检查

        Returns:
            (success: bool, data: Any)
            - success: 检查是否成功
            - data: 响应数据或错误信息
        """
        return self._make_request("GET", "/health")

    def set_auth_token(self, token: str):
        """
        设置认证token（在session中）

        Args:
            token: JWT token
        """
        self._session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_auth_token(self):
        """清除认证token"""
        self._session.headers.pop("Authorization", None)

    def close(self):
        """关闭客户端连接"""
        self._session.close()

    def get_strategies(self, token: Optional[str] = None) -> Tuple[bool, Any]:
        """
        获取策略列表

        Args:
            token: JWT token（如果不提供，使用session中的token）

        Returns:
            (success: bool, data: Any)
            - success: 获取是否成功
            - data: 成功时返回策略列表（List[StrategyListItem]），失败时返回错误信息
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        success, data = self._make_request("GET", "/strategies", headers=headers)
        return success, data

    def download_strategy(self, strategy_id: str, token: Optional[str] = None) -> Tuple[bool, Any]:
        """
        下载策略文件

        Args:
            strategy_id: 策略ID
            token: JWT token（如果不提供，使用session中的token）

        Returns:
            (success: bool, data: Any)
            - success: 下载是否成功
            - data: 成功时返回二进制数据（bytes），失败时返回错误信息
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        url = f"{self.base_url}/strategies/{strategy_id}/download".lstrip("/")

        try:
            _LOGGER.debug(f"Making GET request to download strategy {strategy_id}")
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            _LOGGER.debug(f"Response status: {response.status_code}")

            if response.status_code == 200:
                return True, response.content
            else:
                # 尝试解析错误响应
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                except json.JSONDecodeError:
                    error_msg = response.text or f"HTTP {response.status_code}"

                _LOGGER.error(f"Download strategy failed: {error_msg}")
                return False, error_msg

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            _LOGGER.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            _LOGGER.error(error_msg)
            return False, error_msg

    def get_strategy_key(self, strategy_id: str, token: Optional[str] = None) -> Tuple[bool, Any]:
        """
        获取策略密钥

        Args:
            strategy_id: 策略ID
            token: JWT token（如果不提供，使用session中的token）

        Returns:
            (success: bool, data: Any)
            - success: 获取是否成功
            - data: 成功时返回包含密钥的字典{"key_b64": base64字符串}，失败时返回错误信息
        """
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return self._make_request("GET", f"/strategies/{strategy_id}/key", headers=headers)


class APIConfig:
    """API配置"""

    def __init__(
        self, server_host: str = "localhost", server_port: int = 3000, use_ssl: bool = False
    ):
        """
        初始化API配置

        Args:
            server_host: 服务器主机地址
            server_port: 服务器端口
            use_ssl: 是否使用HTTPS
        """
        self.server_host = server_host
        self.server_port = server_port
        self.use_ssl = use_ssl

    @property
    def base_url(self) -> str:
        """获取API基础URL"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.server_host}:{self.server_port}/api"

    @classmethod
    def from_env(cls) -> "APIConfig":
        """从环境变量创建配置"""
        import os

        server_host = os.getenv("API_SERVER_HOST", "localhost")
        server_port = int(os.getenv("API_SERVER_PORT", "3000"))
        use_ssl = os.getenv("API_SERVER_SSL", "false").lower() == "true"

        return cls(server_host, server_port, use_ssl)
