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


# ── 股票池 ──


def fetch_all_stock_codes() -> List[str]:
    """获取全市场 A 股代码列表。"""
    logger.info("开始获取全市场股票列表")
    df = ak.stock_zh_a_spot_em()
    codes = df["代码"].tolist()
    logger.info("获取到 %d 只股票", len(codes))
    return codes


# ── 日线行情 ──


def fetch_daily_quotes(
    code: str,
    start_date: date,
    end_date: Optional[date] = None,
) -> List[DailyQuote]:
    """获取单只股票的日线行情。

    Args:
        code: 股票代码。
        start_date: 起始日期。
        end_date: 结束日期，默认为当天。

    Returns:
        日线行情列表。
    """
    end = end_date or date.today()

    @retry_on_failure
    def _fetch() -> pd.DataFrame:
        _rate_limit()
        return ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=_format_date(start_date),
            end_date=_format_date(end),
            adjust="qfq",
        )

    df = _fetch()
    if df is None or df.empty:
        return []

    records: List[DailyQuote] = []
    for _, row in df.iterrows():
        try:
            records.append(
                DailyQuote(
                    code=code,
                    name=row.get("名称", ""),
                    date=row["日期"] if isinstance(row["日期"], date) else row["日期"].date(),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=int(row["成交量"]),
                    amount=float(row["成交额"]),
                    change_pct=float(row.get("涨跌幅", 0)),
                    turnover_rate=float(row.get("换手率", 0)),
                )
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning("解析日线数据失败 %s %s: %s", code, row.get("日期", ""), e)
    return records


# ── 龙虎榜 ──


def fetch_lhb_details(trade_date: date) -> List[LHBDetail]:
    """获取指定日期的龙虎榜数据。"""
    @retry_on_failure
    def _fetch() -> pd.DataFrame:
        _rate_limit()
        d = _format_date(trade_date)
        return ak.stock_lhb_detail_em(start_date=d, end_date=d)

    df = _fetch()
    if df is None or df.empty:
        return []

    records: List[LHBDetail] = []
    for _, row in df.iterrows():
        try:
            records.append(
                LHBDetail(
                    code=str(row["代码"]),
                    name=str(row["名称"]),
                    date=row["上榜日"] if isinstance(row["上榜日"], date) else datetime.strptime(str(row["上榜日"]), "%Y-%m-%d").date(),
                    close=float(row.get("收盘价", 0)),
                    change_pct=float(row.get("涨跌幅", 0)),
                    net_buy_amount=float(row.get("龙虎榜净买额", 0)),
                    buy_amount=float(row.get("龙虎榜买入额", 0)),
                    sell_amount=float(row.get("龙虎榜卖出额", 0)),
                    total_amount=float(row.get("龙虎榜成交额", 0)),
                    reason=str(row.get("上榜原因", "")),
                    turnover_rate=float(row.get("换手率", 0)),
                )
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning("解析龙虎榜数据失败 %s: %s", trade_date, e)
    return records


# ── 资金流向 ──


def fetch_fund_flow(code: str, trade_date: date) -> Optional[FundFlow]:
    """获取单只股票某日资金流向。"""
    @retry_on_failure
    def _fetch() -> pd.DataFrame:
        _rate_limit(0.3, 1.0)
        return ak.stock_individual_fund_flow(stock=code, market="sz")

    df = _fetch()
    if df is None or df.empty:
        return None

    target = _format_date(trade_date)
    row = df[df["日期"] == target]
    if row.empty:
        return None

    r = row.iloc[0]
    try:
        return FundFlow(
            code=code,
            name=str(r.get("名称", "")),
            date=trade_date,
            main_net_inflow=float(r.get("主力净流入", 0)),
            retail_net_inflow=float(r.get("小单净流入", 0)),
            main_net_inflow_pct=float(r.get("主力净流入百分比", 0)),
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.warning("解析资金流向失败 %s %s: %s", code, trade_date, e)
        return None


# ── 北向资金 ──


def fetch_north_funds(trade_date: date) -> Optional[NorthFund]:
    """获取北向资金数据。"""
    @retry_on_failure
    def _fetch() -> pd.DataFrame:
        _rate_limit(0.5, 1.5)
        return ak.stock_hsgt_summary_em()

    df = _fetch()
    if df is None or df.empty:
        return None

    target = _format_date(trade_date)
    row = df[df["日期"] == target]
    if row.empty:
        return None

    r = row.iloc[0]
    try:
        return NorthFund(
            date=trade_date,
            sh_net_inflow=float(r.get("沪股通净流入", 0)),
            sz_net_inflow=float(r.get("深股通净流入", 0)),
            total_net_inflow=float(r.get("合计净流入", 0)),
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.warning("解析北向资金失败 %s: %s", trade_date, e)
        return None


# ── 板块行情 ──


def fetch_board_daily(
    board_type: str = "industry",
) -> pd.DataFrame:
    """获取板块行情。"""
    @retry_on_failure
    def _fetch() -> pd.DataFrame:
        _rate_limit(0.5, 1.5)
        if board_type == "concept":
            return ak.stock_board_concept_name_em()
        return ak.stock_board_industry_name_em()

    return _fetch()
