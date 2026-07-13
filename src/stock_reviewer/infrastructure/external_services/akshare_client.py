"""akshare 客户端封装。

统一管理 akshare 调用：重试、限频、错误处理、日志。
所有外部调用走这里，不直接调用 akshare。
"""

import random
import time
from datetime import date, datetime
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar

import akshare as ak
import pandas as pd

from stock_reviewer.core.config import settings
from stock_reviewer.core.logging import logger
from stock_reviewer.domain.entities.models import (
    DailyQuote,
    FundFlow,
    LHBDetail,
    NorthFund,
)

T = TypeVar("T")


def _rate_limit(min_delay: float = 0.0, max_delay: float = 0.0) -> None:
    """限频：随机休眠一段时间。"""
    delay = random.uniform(
        min_delay or settings.request_min_delay,
        max_delay or settings.request_max_delay,
    )
    time.sleep(delay)


def retry_on_failure(
    func: Callable[..., T],
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
) -> Callable[..., T]:
    """重试装饰器：调用失败后等待指数退避再重试。"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        attempts = max_attempts or settings.retry_max_attempts
        delay = base_delay or settings.retry_base_delay
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                logger.warning(
                    "%s 第 %d/%d 次失败: %s",
                    func.__name__, attempt, attempts, e,
                )
                if attempt < attempts:
                    time.sleep(delay * (2 ** (attempt - 1)))
        raise Exception(f"{func.__name__} 重试 {attempts} 次后仍失败") from last_exc

    return wrapper


def _format_date(d: date) -> str:
    """格式化为 akshare 需要的 YYYYMMDD。"""
    return d.strftime("%Y%m%d")


# ── 数据获取（当前版本未启用，后续迭代实现） ──
#
# 以下函数保留签名和文档，内部抛出 NotImplementedError。
# 当前使用通达信导入模式，请参考 adapters/tdx_importer.py。


def fetch_all_stock_codes() -> List[str]:
    """获取全市场 A 股代码列表。"""
    raise NotImplementedError("在线获取暂未启用，请使用通达信导入模式")


def fetch_daily_quotes(
    code: str,
    start_date: date,
    end_date: Optional[date] = None,
) -> List[DailyQuote]:
    """获取单只股票的日线行情。"""
    raise NotImplementedError("在线获取暂未启用，请使用通达信导入模式")


def fetch_lhb_details(trade_date: date) -> List[LHBDetail]:
    """获取指定日期的龙虎榜数据。"""
    raise NotImplementedError("在线获取暂未启用，请使用通达信导入模式")


def fetch_fund_flow(code: str, trade_date: date) -> Optional[FundFlow]:
    """获取单只股票某日资金流向。"""
    raise NotImplementedError("在线获取暂未启用，请使用通达信导入模式")


def fetch_north_funds(trade_date: date) -> Optional[NorthFund]:
    """获取北向资金数据。"""
    raise NotImplementedError("在线获取暂未启用，请使用通达信导入模式")


def fetch_board_daily(
    board_type: str = "industry",
) -> pd.DataFrame:
    """获取板块行情。"""
    raise NotImplementedError("在线获取暂未启用，请使用通达信导入模式")
