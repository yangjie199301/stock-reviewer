"""季度数据采集编排器。

负责基本面（财报）数据采集，频次低，按季度触发。
"""

from datetime import date
from typing import List, Optional

from stock_reviewer.core.logging import logger
from stock_reviewer.domain.entities.models import FinancialReport
from stock_reviewer.infrastructure.database.repositories.sqlite_repositories import (
    SqliteFinancialReportRepository,
    SqliteDataMetaRepository,
)
from stock_reviewer.infrastructure.external_services import akshare_client


class QuarterlyCollector:
    """季度数据采集编排器。"""

    def __init__(self) -> None:
        self.repo = SqliteFinancialReportRepository()
        self.meta_repo = SqliteDataMetaRepository()

    def collect_all(self, codes: List[str]) -> dict:
        """采集全部股票的最新财报。

        只拉取最新一个报告期（判断是否已进入披露期）。
        首次运行时拉取近 5 年历史财报。

        Args:
            codes: 股票代码列表。

        Returns:
            采集结果摘要。
        """
        logger.info("===== 开始季度财报采集 =====")
        total_written = 0
        fail_count = 0

        for idx, code in enumerate(codes, 1):
            try:
                latest = self.meta_repo.get("financial_reports", code)
                if latest:
                    # 增量：只判断最新季度
                    new_records = self._fetch_latest_quarter(code)
                else:
                    # 首次：拉取近 5 年
                    new_records = self._fetch_historical(code)

                if new_records:
                    written = self.repo.batch_upsert(new_records)
                    total_written += written
                    max_date = max(r.report_date for r in new_records)
                    self.meta_repo.set("financial_reports", code, max_date)
            except Exception as e:
                fail_count += 1
                logger.error("采集 %s 财报失败: %s", code, e)

            if idx % 100 == 0:
                logger.info("财报进度: %d/%d", idx, len(codes))

        msg = f"财报采集完成: 写入 {total_written} 条, 失败 {fail_count} 只"
        logger.info(msg)
        return {"financial_reports": msg}

    def _fetch_latest_quarter(self, code: str) -> List[FinancialReport]:
        """拉取最新季度财报（待实现具体 akshare 接口映射）。"""
        # TODO: 对接 akshare 财报接口
        return []

    def _fetch_historical(self, code: str) -> List[FinancialReport]:
        """拉取过去 5 年财报。"""
        # TODO: 对接 akshare 财报接口
        return []
