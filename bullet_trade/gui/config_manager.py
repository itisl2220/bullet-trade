"""
GUI 配置管理器
用于管理GUI配置的本地缓存
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为 ~/.bullet-trade/gui_config.json
        """
        if config_file is None:
            home_dir = Path.home()
            config_dir = home_dir / ".bullet-trade"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "gui_config.json"

        self.config_file = Path(config_file)
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """从文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}
        else:
            self._config = {}
            # 初始化默认配置
            self._init_defaults()

    def _init_defaults(self):
        """初始化默认配置"""
        self._config = {
            "live_mode": "dry_run",
            "data_provider": "jqdata",
            "data_cache_dir": "~/.bullet-trade/cache",
            "qmt_host": "127.0.0.1",
            "qmt_port": 58610,
            "jqdata_username": "",
            "jqdata_password": "",
            "broker": "simulator",
            "qmt_account_id": "",
            "qmt_account_type": "stock",
            "qmt_data_path": "",
            "qmt_server_host": "127.0.0.1",
            "qmt_server_port": 58620,
            "qmt_server_token": "",
            "simulator_initial_cash": 1000000,
            "max_order_value": 100000,
            "max_daily_trade_value": 500000,
            "max_daily_trades": 100,
            "max_stock_count": 20,
            "max_position_ratio": 20.0,
            "stop_loss_ratio": 5.0,
            "log_dir": "./logs",
            "log_level": "INFO",
            "runtime_dir": "./runtime",
            "debug": False,
            # API服务器配置
            "api_server_host": "127.0.0.1",
            "api_server_port": 3000,
            "api_server_ssl": False,
        }

    def save(self):
        """保存配置到文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def update(self, config: Dict[str, Any]):
        """批量更新配置"""
        self._config.update(config)

    def apply_to_env(self):
        """将配置应用到环境变量"""
        # 映射配置键到环境变量名
        env_mapping = {
            "live_mode": "LIVE_MODE",
            "data_provider": "DEFAULT_DATA_PROVIDER",
            "data_cache_dir": "DATA_CACHE_DIR",
            "qmt_host": "QMT_HOST",
            "qmt_port": "QMT_PORT",
            "jqdata_username": "JQDATA_USERNAME",
            "jqdata_password": "JQDATA_PASSWORD",
            "broker": "DEFAULT_BROKER",
            "qmt_account_id": "QMT_ACCOUNT_ID",
            "qmt_account_type": "QMT_ACCOUNT_TYPE",
            "qmt_data_path": "QMT_DATA_PATH",
            "qmt_server_host": "QMT_SERVER_HOST",
            "qmt_server_port": "QMT_SERVER_PORT",
            "qmt_server_token": "QMT_SERVER_TOKEN",
            "simulator_initial_cash": "SIMULATOR_INITIAL_CASH",
            "max_order_value": "MAX_ORDER_VALUE",
            "max_daily_trade_value": "MAX_DAILY_TRADE_VALUE",
            "max_daily_trades": "MAX_DAILY_TRADES",
            "max_stock_count": "MAX_STOCK_COUNT",
            "max_position_ratio": "MAX_POSITION_RATIO",
            "stop_loss_ratio": "STOP_LOSS_RATIO",
            "log_dir": "LOG_DIR",
            "log_level": "LOG_LEVEL",
            "runtime_dir": "RUNTIME_DIR",
            "debug": "DEBUG",
            "api_server_host": "API_SERVER_HOST",
            "api_server_port": "API_SERVER_PORT",
            "api_server_ssl": "API_SERVER_SSL",
        }

        for config_key, env_key in env_mapping.items():
            value = self._config.get(config_key)
            if value is not None:
                if isinstance(value, bool):
                    os.environ[env_key] = "true" if value else "false"
                elif isinstance(value, (int, float)):
                    os.environ[env_key] = str(value)
                elif value:  # 非空字符串
                    os.environ[env_key] = str(value)
