"""应用配置。

从环境变量加载，支持默认值。
所有配置集中管理，各模块通过 `settings` 对象读取。
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    # ── 数据库 ──
    db_path: str = os.getenv("DB_PATH", "data/quant_data.db")

    # ── 股票池 ──
    stock_pool: List[str] = field(default_factory=lambda: [])  # 空 = 全市场
    test_mode: bool = os.getenv("TEST_MODE", "true").lower() == "true"
    test_stock_count: int = int(os.getenv("TEST_STOCK_COUNT", "100"))

    # ── 请求频率控制（秒） ──
    request_min_delay: float = float(os.getenv("REQUEST_MIN_DELAY", "0.5"))
    request_max_delay: float = float(os.getenv("REQUEST_MAX_DELAY", "2.0"))

    # ── 重试配置 ──
    retry_max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    retry_base_delay: float = float(os.getenv("RETRY_BASE_DELAY", "5.0"))

    # ── 日志 ──
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")

    # ── 外部数据源 ──
    tushare_token: str = os.getenv("TUSHARE_TOKEN", "")


settings = Settings()
