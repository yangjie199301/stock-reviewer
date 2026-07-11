"""数据查询 + 整合服务。

提供对外的查询接口，以及将多表数据组装为"一份完整当日数据"的能力。
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from stock_reviewer.domain.entities.models import (
    DailyQuote,
    FundFlow,
    LHBDetail,
    NorthFund,
    BoardDaily,
)
from stock_reviewer.infrastructure.database.repositories.sqlite_repositories import (
    SqliteDailyQuoteRepository,
    SqliteLHBRepository,
    SqliteFundFlowRepository,
    SqliteNorthFundRepository,
    SqliteBoardDailyRepository,
)


@dataclass
class DailySummary:
    """整合后的单日数据结构，供复盘使用。"""
    trade_date: date
    north_fund: Optional[NorthFund] = None
    lhb_records: List[LHBDetail] = field(default_factory=list)
    industry_boards: List[BoardDaily] = field(default_factory=list)
    concept_boards: List[BoardDaily] = field(default_factory=list)
    top_gainers: List[DailyQuote] = field(default_factory=list)   # 涨幅前 10
    top_volumes: List[DailyQuote] = field(default_factory=list)   # 成交额前 10
    # 扩展字段：可通过 metadata 传递其他信息
    metadata: Dict = field(default_factory=dict)


class QueryService:
    """数据查询服务。"""

    def __init__(self) -> None:
        self.quote_repo = SqliteDailyQuoteRepository()
        self.lhb_repo = SqliteLHBRepository()
        self.fund_flow_repo = SqliteFundFlowRepository()
        self.north_fund_repo = SqliteNorthFundRepository()
        self.board_repo = SqliteBoardDailyRepository()

    def get_daily_summary(self, trade_date: date) -> DailySummary:
        """获取指定交易日的整合数据。

        Args:
            trade_date: 交易日期。

        Returns:
            整合后的单日数据对象。各字段可能为空（数据不存在时）。
        """
        summary = DailySummary(trade_date=trade_date)

        # 北向资金
        funds = self.north_fund_repo.find_by_date_range(trade_date, trade_date)
        if funds:
            summary.north_fund = funds[0]

        # 龙虎榜
        summary.lhb_records = self.lhb_repo.find_by_date(trade_date)

        # 板块行情
        boards = self.board_repo.find_by_date(trade_date)
        summary.industry_boards = [b for b in boards if b.board_type == "industry"]
        summary.concept_boards = [b for b in boards if b.board_type == "concept"]

        # TODO: top_gainers / top_volumes — 需全市场查询接口支持
        # 当前 daily_quotes 是按 code 组织的，全市场查询需要额外的表扫描

        return summary

    def get_stock_quotes(
        self, code: str, start: date, end: date
    ) -> List[DailyQuote]:
        """获取某只股票一段时间内的日线行情。

        Args:
            code: 股票代码。
            start: 起始日期。
            end: 结束日期。

        Returns:
            日线行情列表。
        """
        return self.quote_repo.find_by_code_and_date_range(code, start, end)

    def get_fund_flow(
        self, code: str, query_date: date
    ) -> Optional[FundFlow]:
        """获取某只股票某日的资金流向。

        Args:
            code: 股票代码。
            query_date: 交易日期。

        Returns:
            资金流向记录，没有则返回 None。
        """
        return self.fund_flow_repo.find_by_code_and_date(code, query_date)
