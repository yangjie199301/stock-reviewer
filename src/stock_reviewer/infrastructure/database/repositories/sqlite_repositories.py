"""SQLite 仓库实现。

所有仓库接口的 SQLite 实现，每个仓库对应一个表。
"""

from datetime import date
from typing import List, Optional

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
from stock_reviewer.infrastructure.database.connection import get_connection


class SqliteDailyQuoteRepository:
    """日线行情仓库。"""

    def batch_upsert(self, records: List[DailyQuote]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO daily_quotes
                   (code, name, date, open, high, low, close, volume, amount, change_pct, turnover_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.code, r.name, r.date.isoformat(), r.open, r.high, r.low,
                 r.close, r.volume, r.amount, r.change_pct, r.turnover_rate),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_code_and_date_range(
        self, code: str, start: date, end: date
    ) -> List[DailyQuote]:
        conn = get_connection()
        rows = conn.execute(
            """SELECT code, name, date, open, high, low, close, volume, amount, change_pct, turnover_rate
               FROM daily_quotes WHERE code = ? AND date BETWEEN ? AND ? ORDER BY date""",
            (code, start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_quote(r) for r in rows]

    def get_latest_date(self, code: str) -> Optional[date]:
        conn = get_connection()
        row = conn.execute(
            "SELECT MAX(date) FROM daily_quotes WHERE code = ?", (code,)
        ).fetchone()
        if row and row[0]:
            return date.fromisoformat(row[0])
        return None


class SqliteLHBRepository:
    """龙虎榜仓库。"""

    def batch_upsert(self, records: List[LHBDetail]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO lhb_details
                   (code, name, date, close, change_pct, net_buy_amount, buy_amount, sell_amount, total_amount, reason, turnover_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.code, r.name, r.date.isoformat(), r.close, r.change_pct,
                 r.net_buy_amount, r.buy_amount, r.sell_amount, r.total_amount,
                 r.reason, r.turnover_rate),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_date(self, query_date: date) -> List[LHBDetail]:
        conn = get_connection()
        rows = conn.execute(
            """SELECT code, name, date, close, change_pct, net_buy_amount, buy_amount, sell_amount, total_amount, reason, turnover_rate
               FROM lhb_details WHERE date = ?""",
            (query_date.isoformat(),),
        ).fetchall()
        return [_row_to_lhb(r) for r in rows]


class SqliteFundFlowRepository:
    """资金流向仓库。"""

    def batch_upsert(self, records: List[FundFlow]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO fund_flows
                   (code, name, date, main_net_inflow, retail_net_inflow, main_net_inflow_pct)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r.code, r.name, r.date.isoformat(), r.main_net_inflow,
                 r.retail_net_inflow, r.main_net_inflow_pct),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_code_and_date(self, code: str, query_date: date) -> Optional[FundFlow]:
        conn = get_connection()
        row = conn.execute(
            """SELECT code, name, date, main_net_inflow, retail_net_inflow, main_net_inflow_pct
               FROM fund_flows WHERE code = ? AND date = ?""",
            (code, query_date.isoformat()),
        ).fetchone()
        if row:
            return _row_to_fund_flow(row)
        return None


class SqliteNorthFundRepository:
    """北向资金仓库。"""

    def batch_upsert(self, records: List[NorthFund]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO north_funds
                   (date, sh_net_inflow, sz_net_inflow, total_net_inflow)
                   VALUES (?, ?, ?, ?)""",
                (r.date.isoformat(), r.sh_net_inflow, r.sz_net_inflow, r.total_net_inflow),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_date_range(self, start: date, end: date) -> List[NorthFund]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT date, sh_net_inflow, sz_net_inflow, total_net_inflow FROM north_funds WHERE date BETWEEN ? AND ? ORDER BY date",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_north_fund(r) for r in rows]


class SqliteBoardDailyRepository:
    """板块行情仓库。"""

    def batch_upsert(self, records: List[BoardDaily]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO board_daily
                   (board_name, board_type, date, change_pct, up_count, down_count, leader_code, leader_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.board_name, r.board_type, r.date.isoformat(), r.change_pct,
                 r.up_count, r.down_count, r.leader_code, r.leader_name),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_date(self, query_date: date) -> List[BoardDaily]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT board_name, board_type, date, change_pct, up_count, down_count, leader_code, leader_name FROM board_daily WHERE date = ?",
            (query_date.isoformat(),),
        ).fetchall()
        return [_row_to_board(r) for r in rows]


class SqlitePolicyRepository:
    """政策资讯仓库。"""

    def batch_upsert(self, records: List[Policy]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO policies (url, title, publish_date, source, summary, keywords)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r.url, r.title, r.publish_date.isoformat(), r.source, r.summary, r.keywords),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_date_range(self, start: date, end: date) -> List[Policy]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT url, title, publish_date, source, summary, keywords FROM policies WHERE publish_date BETWEEN ? AND ? ORDER BY publish_date DESC",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_policy(r) for r in rows]


class SqliteResearchReportRepository:
    """研报仓库。"""

    def batch_upsert(self, records: List[ResearchReport]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO research_reports
                   (url, title, stock_code, stock_name, institution, publish_date, summary, rating, keywords)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.url, r.title, r.stock_code, r.stock_name, r.institution,
                 r.publish_date.isoformat(), r.summary, r.rating, r.keywords),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_date_range(self, start: date, end: date) -> List[ResearchReport]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT url, title, stock_code, stock_name, institution, publish_date, summary, rating, keywords FROM research_reports WHERE publish_date BETWEEN ? AND ? ORDER BY publish_date DESC",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_row_to_report(r) for r in rows]


class SqliteFinancialReportRepository:
    """财报仓库。"""

    def batch_upsert(self, records: List[FinancialReport]) -> int:
        conn = get_connection()
        count = 0
        for r in records:
            conn.execute(
                """INSERT OR IGNORE INTO financial_reports
                   (code, name, report_date, report_type, revenue, net_profit, total_assets, total_liabilities, equity, roe, gross_margin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.code, r.name, r.report_date.isoformat(), r.report_type,
                 r.revenue, r.net_profit, r.total_assets, r.total_liabilities,
                 r.equity, r.roe, r.gross_margin),
            )
            count += conn.total_changes
        conn.commit()
        return count

    def find_by_code(self, code: str) -> List[FinancialReport]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT code, name, report_date, report_type, revenue, net_profit, total_assets, total_liabilities, equity, roe, gross_margin FROM financial_reports WHERE code = ? ORDER BY report_date DESC",
            (code,),
        ).fetchall()
        return [_row_to_financial(r) for r in rows]

    def get_latest_report_date(self, code: str) -> Optional[date]:
        conn = get_connection()
        row = conn.execute(
            "SELECT MAX(report_date) FROM financial_reports WHERE code = ?", (code,)
        ).fetchone()
        if row and row[0]:
            return date.fromisoformat(row[0])
        return None


class SqliteDataMetaRepository:
    """数据更新元信息仓库。"""

    def get(self, table_name: str, code: str) -> Optional[DataMeta]:
        conn = get_connection()
        row = conn.execute(
            "SELECT table_name, code, latest_date FROM data_meta WHERE table_name = ? AND code = ?",
            (table_name, code),
        ).fetchone()
        if row:
            return DataMeta(
                table_name=row[0],
                code=row[1],
                latest_date=date.fromisoformat(row[2]),
            )
        return None

    def set(self, table_name: str, code: str, latest_date: date) -> None:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO data_meta (table_name, code, latest_date) VALUES (?, ?, ?)",
            (table_name, code, latest_date.isoformat()),
        )
        conn.commit()


# ── 行转实体辅助函数 ──


def _row_to_quote(row) -> DailyQuote:
    return DailyQuote(
        code=row[0], name=row[1], date=date.fromisoformat(row[2]),
        open=row[3], high=row[4], low=row[5], close=row[6],
        volume=row[7], amount=row[8], change_pct=row[9], turnover_rate=row[10],
    )


def _row_to_lhb(row) -> LHBDetail:
    return LHBDetail(
        code=row[0], name=row[1], date=date.fromisoformat(row[2]),
        close=row[3], change_pct=row[4], net_buy_amount=row[5],
        buy_amount=row[6], sell_amount=row[7], total_amount=row[8],
        reason=row[9], turnover_rate=row[10],
    )


def _row_to_fund_flow(row) -> FundFlow:
    return FundFlow(
        code=row[0], name=row[1], date=date.fromisoformat(row[2]),
        main_net_inflow=row[3], retail_net_inflow=row[4], main_net_inflow_pct=row[5],
    )


def _row_to_north_fund(row) -> NorthFund:
    return NorthFund(
        date=date.fromisoformat(row[0]), sh_net_inflow=row[1],
        sz_net_inflow=row[2], total_net_inflow=row[3],
    )


def _row_to_board(row) -> BoardDaily:
    return BoardDaily(
        board_name=row[0], board_type=row[1], date=date.fromisoformat(row[2]),
        change_pct=row[3], up_count=row[4], down_count=row[5],
        leader_code=row[6], leader_name=row[7],
    )


def _row_to_policy(row) -> Policy:
    return Policy(
        url=row[0], title=row[1], publish_date=date.fromisoformat(row[2]),
        source=row[3], summary=row[4], keywords=row[5],
    )


def _row_to_report(row) -> ResearchReport:
    return ResearchReport(
        url=row[0], title=row[1], stock_code=row[2], stock_name=row[3],
        institution=row[4], publish_date=date.fromisoformat(row[5]),
        summary=row[6], rating=row[7], keywords=row[8],
    )


def _row_to_financial(row) -> FinancialReport:
    return FinancialReport(
        code=row[0], name=row[1], report_date=date.fromisoformat(row[2]),
        report_type=row[3], revenue=row[4], net_profit=row[5],
        total_assets=row[6], total_liabilities=row[7], equity=row[8],
        roe=row[9], gross_margin=row[10],
    )
