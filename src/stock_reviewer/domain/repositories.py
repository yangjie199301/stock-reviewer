"""仓库接口定义。

使用 Protocol 定义接口契约，基础设施层实现。
应用层只依赖接口，不依赖具体实现。
"""

from typing import List, Optional, Protocol
from datetime import date

from stock_reviewer.domain.entities.models import (
    DailyQuote,
    LHBDetail,
    FundFlow,
    NorthFund,
    BoardDaily,
    Policy,
    ResearchReport,
    FinancialReport,
    DataMeta,
)


class DailyQuoteRepository(Protocol):
    def batch_upsert(self, records: List[DailyQuote]) -> int:
        """批量写入日线行情，已存在的记录忽略。返回写入行数。"""

    def find_by_code_and_date_range(
        self, code: str, start: date, end: date
    ) -> List[DailyQuote]:
        """查询某只股票在日期范围内的行情。"""

    def get_latest_date(self, code: str) -> Optional[date]:
        """获取某只股票已存储的最新日期。"""


class LHBRepository(Protocol):
    def batch_upsert(self, records: List[LHBDetail]) -> int:
        """批量写入龙虎榜数据。"""

    def find_by_date(self, query_date: date) -> List[LHBDetail]:
        """查询指定日期的龙虎榜。"""


class FundFlowRepository(Protocol):
    def batch_upsert(self, records: List[FundFlow]) -> int:
        """批量写入资金流向数据。"""

    def find_by_code_and_date(
        self, code: str, query_date: date
    ) -> Optional[FundFlow]:
        """查询某只股票某日的资金流向。"""


class NorthFundRepository(Protocol):
    def batch_upsert(self, records: List[NorthFund]) -> int:
        """批量写入北向资金数据。"""

    def find_by_date_range(
        self, start: date, end: date
    ) -> List[NorthFund]:
        """查询日期范围内的北向资金。"""


class BoardDailyRepository(Protocol):
    def batch_upsert(self, records: List[BoardDaily]) -> int:
        """批量写入板块行情。"""

    def find_by_date(self, query_date: date) -> List[BoardDaily]:
        """查询指定日期的板块行情。"""


class PolicyRepository(Protocol):
    def batch_upsert(self, records: List[Policy]) -> int:
        """批量写入政策资讯。"""

    def find_by_date_range(
        self, start: date, end: date
    ) -> List[Policy]:
        """查询日期范围内的政策。"""


class ResearchReportRepository(Protocol):
    def batch_upsert(self, records: List[ResearchReport]) -> int:
        """批量写入研报。"""

    def find_by_date_range(
        self, start: date, end: date
    ) -> List[ResearchReport]:
        """查询日期范围内的研报。"""


class FinancialReportRepository(Protocol):
    def batch_upsert(self, records: List[FinancialReport]) -> int:
        """批量写入财报数据。"""

    def find_by_code(self, code: str) -> List[FinancialReport]:
        """查询某只股票的历史财报。"""

    def get_latest_report_date(self, code: str) -> Optional[date]:
        """获取某只股票已存储的最新财报报告期。"""


class DataMetaRepository(Protocol):
    def get(self, table_name: str, code: str) -> Optional[DataMeta]:
        """获取某张表某只股票的更新元信息。"""

    def set(self, table_name: str, code: str, latest_date: date) -> None:
        """设置或更新元信息。"""
