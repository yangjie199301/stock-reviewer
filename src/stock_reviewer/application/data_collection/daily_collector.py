"""每日数据采集编排器。

按顺序采集各类数据，每步独立 try-except，单步失败不影响后续。
"""

from datetime import date, timedelta
from typing import List, Optional

from stock_reviewer.core.config import settings
from stock_reviewer.core.logging import logger
from stock_reviewer.domain.entities.models import BoardDaily
from stock_reviewer.infrastructure.database.repositories.sqlite_repositories import (
    SqliteDailyQuoteRepository,
    SqliteLHBRepository,
    SqliteFundFlowRepository,
    SqliteNorthFundRepository,
    SqliteBoardDailyRepository,
    SqliteDataMetaRepository,
)
from stock_reviewer.infrastructure.external_services import akshare_client


class DailyCollector:
    """每日数据采集编排器。"""

    def __init__(self) -> None:
        self.quote_repo = SqliteDailyQuoteRepository()
        self.lhb_repo = SqliteLHBRepository()
        self.fund_flow_repo = SqliteFundFlowRepository()
        self.north_fund_repo = SqliteNorthFundRepository()
        self.board_repo = SqliteBoardDailyRepository()
        self.meta_repo = SqliteDataMetaRepository()

    def collect_all(self, trade_date: date) -> dict:
        """采集指定交易日所有数据。

        Args:
            trade_date: 交易日。

        Returns:
            各数据类型的采集结果摘要。
        """
        summary: dict = {}

        logger.info("===== 开始采集 %s 数据 =====", trade_date)

        summary["board"] = self._collect_boards(trade_date)
        summary["north_fund"] = "skip" if summary.get("north_fund") == "skip" else self._collect_north_funds(trade_date)
        summary["lhb"] = self._collect_lhb(trade_date)
        summary["daily_quotes"] = self._collect_daily_quotes(trade_date)

        # 统计
        success = sum(
            1 for v in summary.values() if isinstance(v, str) and "完成" in v
        )
        total = len(summary)
        logger.info("===== %s 采集完成: %d/%d 成功 =====", trade_date, success, total)
        summary["_stats"] = {"success": success, "total": total}
        return summary

    # ── 内部采集方法 ──

    def _get_stock_list(self) -> List[str]:
        """获取待采集的股票列表。"""
        if settings.test_mode:
            all_codes = akshare_client.fetch_all_stock_codes()
            codes = all_codes[: settings.test_stock_count]
            logger.info("测试模式：仅采集前 %d 只股票", len(codes))
        else:
            codes = akshare_client.fetch_all_stock_codes()
        return codes

    def _get_incremental_start(self, code: str) -> date:
        """获取增量采集的起始日期。"""
        latest = self.quote_repo.get_latest_date(code)
        if latest:
            return latest + timedelta(days=1)
        # 首次采集：拉近 1 年数据
        return date.today() - timedelta(days=365)

    def _collect_daily_quotes(self, trade_date: date) -> str:
        """采集全市场日线行情（增量）。"""
        logger.info("开始采集日线行情 %s", trade_date)
        codes = self._get_stock_list()
        total_count = 0
        fail_count = 0

        for idx, code in enumerate(codes, 1):
            try:
                start = self._get_incremental_start(code)
                if start > trade_date:
                    continue  # 已是最新
                records = akshare_client.fetch_daily_quotes(code, start, trade_date)
                if records:
                    written = self.quote_repo.batch_upsert(records)
                    total_count += written
                    # 更新元信息
                    self.meta_repo.set("daily_quotes", code, trade_date)
            except Exception as e:
                fail_count += 1
                logger.error("采集 %s 行情失败: %s", code, e)

            if idx % 50 == 0:
                logger.info("日线行情进度: %d/%d", idx, len(codes))

        msg = f"日线行情完成: 写入 {total_count} 条, 失败 {fail_count} 只"
        logger.info(msg)
        return msg

    def _collect_lhb(self, trade_date: date) -> str:
        """采集龙虎榜数据。"""
        try:
            records = akshare_client.fetch_lhb_details(trade_date)
            if records:
                written = self.lhb_repo.batch_upsert(records)
                msg = f"龙虎榜完成: {len(records)} 只, 写入 {written} 条"
            else:
                msg = "龙虎榜: 当日无数据"
            logger.info(msg)
            return msg
        except Exception as e:
            msg = f"龙虎榜采集失败: {e}"
            logger.error(msg)
            return msg

    def _collect_north_funds(self, trade_date: date) -> str:
        """采集北向资金数据。"""
        try:
            record = akshare_client.fetch_north_funds(trade_date)
            if record:
                self.north_fund_repo.batch_upsert([record])
                msg = (
                    f"北向资金完成: 沪 {record.sh_net_inflow/1e8:.2f}亿, "
                    f"深 {record.sz_net_inflow/1e8:.2f}亿"
                )
            else:
                msg = "北向资金: 当日无数据"
            logger.info(msg)
            return msg
        except Exception as e:
            msg = f"北向资金采集失败: {e}"
            logger.error(msg)
            return msg

    def _collect_boards(self, trade_date: date) -> str:
        """采集板块行情。"""
        try:
            records: List[BoardDaily] = []
            for board_type in ("industry", "concept"):
                df = akshare_client.fetch_board_daily(board_type)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        records.append(
                            BoardDaily(
                                board_name=str(row.get("板块名称", "")),
                                board_type=board_type,
                                date=trade_date,
                                change_pct=float(row.get("涨跌幅", 0)),
                                up_count=int(row.get("上涨家数", 0)),
                                down_count=int(row.get("下跌家数", 0)),
                            )
                        )
            if records:
                written = self.board_repo.batch_upsert(records)
                msg = f"板块行情完成: {len(records)} 个板块, 写入 {written} 条"
            else:
                msg = "板块行情: 无数据"
            logger.info(msg)
            return msg
        except Exception as e:
            msg = f"板块行情采集失败: {e}"
            logger.error(msg)
            return msg
