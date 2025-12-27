"""
策略管理器 - 处理策略相关的业务逻辑

将UI逻辑和业务逻辑分离，提供策略下载、解密、本地执行等功能
"""

import logging
from typing import Optional, Callable, Dict, Tuple, List


class StrategyListItem:
    """策略列表项"""

    def __init__(self, id: str, name: str, meta: Optional[str], is_active: bool):
        self.id = id
        self.name = name
        self.meta = meta
        self.is_active = is_active


_logger = logging.getLogger(__name__)


class StrategyManager:
    """策略管理器，处理策略相关的业务逻辑"""

    def __init__(self, auth_manager):
        """
        初始化策略管理器

        Args:
            auth_manager: 认证管理器，提供API客户端
        """
        self.auth_manager = auth_manager
        self.downloaded_strategies: Dict[str, str] = {}  # 缓存已下载的策略

        # UI回调函数
        self.on_status_update: Optional[Callable[[str, str], None]] = None
        self.on_progress_message: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        self.on_success: Optional[Callable[[str, str], None]] = None
        self.on_strategy_list_updated: Optional[Callable[[List[StrategyListItem]], None]] = None

    def set_ui_callbacks(
        self,
        on_status_update: Optional[Callable[[str, str], None]] = None,
        on_progress_message: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        on_success: Optional[Callable[[str, str], None]] = None,
        on_strategy_list_updated: Optional[Callable[[List[StrategyListItem]], None]] = None,
    ):
        """设置UI回调函数"""
        self.on_status_update = on_status_update
        self.on_progress_message = on_progress_message
        self.on_error = on_error
        self.on_success = on_success
        self.on_strategy_list_updated = on_strategy_list_updated

    def _has_api_client(self) -> bool:
        """检查是否有可用的API客户端"""
        return (
            hasattr(self, "auth_manager")
            and self.auth_manager
            and getattr(self.auth_manager, "api_client", None)
        )

    def refresh_remote_list(self) -> bool:
        """
        刷新远程策略列表

        Returns:
            bool: 是否成功
        """
        if not self._has_api_client():
            if self.on_error:
                self.on_error("未认证", "请先登录以访问远端策略列表")
            return False

        try:
            success, data = self.auth_manager.api_client.get_strategies()
            if not success:
                if self.on_error:
                    self.on_error("请求失败", f"无法获取远端策略列表: {data}")
                return False

            # 规范化为 StrategyListItem 列表，兼容 api_client 返回 dict 的情况
            normalized = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        s = StrategyListItem(
                            id=item.get("id", ""),
                            name=item.get("name", ""),
                            meta=item.get("meta"),
                            is_active=item.get("is_active", False),
                        )
                    elif isinstance(item, StrategyListItem):
                        s = item
                    else:
                        # 支持带属性的对象（保守处理）
                        s = StrategyListItem(
                            id=getattr(item, "id", "") or "",
                            name=getattr(item, "name", "") or "",
                            meta=getattr(item, "meta", None),
                            is_active=getattr(item, "is_active", False),
                        )
                    normalized.append(s)
            else:
                # 非列表结果直接传递（回调需自行处理）
                normalized = data

            if self.on_strategy_list_updated:
                self.on_strategy_list_updated(normalized)

            return True

        except Exception as e:
            if self.on_error:
                self.on_error("请求失败", f"无法获取远端策略列表: {e}")
            return False

    def download_strategy(self, strategy_id: str) -> bool:
        """
        下载并验证远程策略

        注意：此方法下载策略并在内存中解密以验证完整性，
        但不会返回解密后的代码，以保护远端策略的知识产权。

        Args:
            strategy_id: 策略ID

        Returns:
            bool: 是否成功下载并验证策略
        """
        if not strategy_id:
            if self.on_error:
                self.on_error("参数错误", "请先选择要下载的远端策略")
            return False

        if not self._has_api_client():
            if self.on_error:
                self.on_error("未认证", "请先登录以下载策略")
            return False

        # 更新状态
        if self.on_status_update:
            self.on_status_update("下载中", "正在下载加密策略文件...")

        try:
            # 下载策略文件
            success, encrypted_data = self.auth_manager.api_client.download_strategy(strategy_id)
            if not success:
                error_msg = f"下载策略失败: {encrypted_data}"
                if self.on_status_update:
                    self.on_status_update("下载失败", error_msg)
                if self.on_error:
                    self.on_error("下载失败", error_msg)
                return False

            if self.on_progress_message:
                self.on_progress_message("正在获取解密密钥...")

            # 获取解密密钥
            success, key_data = self.auth_manager.api_client.get_strategy_key(strategy_id)
            if not success:
                error_msg = f"获取密钥失败: {key_data}"
                if self.on_status_update:
                    self.on_status_update("下载失败", error_msg)
                if self.on_error:
                    self.on_error("下载失败", error_msg)
                return False

            key_b64 = key_data.get("key_b64")
            if not key_b64:
                error_msg = "无法获取解密密钥"
                if self.on_status_update:
                    self.on_status_update("下载失败", error_msg)
                if self.on_error:
                    self.on_error("下载失败", error_msg)
                return False

            if self.on_progress_message:
                self.on_progress_message("正在验证策略文件...")

            # 解密策略文件以验证完整性（不返回解密后的代码）
            decrypted_code = self._decrypt_strategy(encrypted_data, key_b64)

            # 只缓存策略ID，不缓存解密后的代码
            self.downloaded_strategies[strategy_id] = "[PROTECTED]"

            # 更新UI为成功状态
            if self.on_status_update:
                self.on_status_update("下载完成", "策略已下载并验证完整性")
            if self.on_success:
                self.on_success("成功", "策略已下载，可以在回测或实盘中使用")

            return True

        except Exception as e:
            error_msg = str(e)
            if self.on_status_update:
                self.on_status_update("下载失败", f"下载失败: {error_msg}")
            if self.on_error:
                self.on_error("下载失败", f"无法下载策略: {error_msg}")
            return False

    def is_strategy_downloaded(self, strategy_id: str) -> bool:
        """
        检查策略是否已下载

        Args:
            strategy_id: 策略ID

        Returns:
            是否已下载
        """
        return strategy_id in self.downloaded_strategies

    def clear_download_cache(self):
        """清除下载缓存"""
        self.downloaded_strategies.clear()
        if self.on_status_update:
            self.on_status_update("未下载", "")

    def _decrypt_strategy(self, encrypted_data: bytes, key_b64: str) -> str:
        """解密策略文件"""
        try:
            # 使用高层AESGCM接口更可靠地处理nonce/tag等细节
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            import base64

            # 解密密钥
            key = base64.b64decode(key_b64)

            # 最小长度：nonce(12) + tag(16)
            if len(encrypted_data) < 12 + 16:
                raise Exception("加密数据格式错误")

            nonce = encrypted_data[:12]
            tag = encrypted_data[-16:]
            ciphertext = encrypted_data[12:-16]

            aesgcm = AESGCM(key)
            # AESGCM.decrypt expects ciphertext||tag as the data argument, but many libraries
            # expect ciphertext and tag concatenated; here we pass ciphertext + tag for compatibility.
            plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)

            return plaintext.decode("utf-8")

        except Exception as e:
            raise Exception(f"解密失败: {e}")
