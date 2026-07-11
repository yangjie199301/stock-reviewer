"""数据库建表 DDL。

所有表的创建脚本集中在此，初始化时调用。
"""

from stock_reviewer.infrastructure.database.connection import get_connection


from typing import Dict

CREATE_TABLE_SQL: Dict[str, str] = {
    "daily_quotes": """
        CREATE TABLE IF NOT EXISTS daily_quotes (
            code         TEXT NOT NULL,
            name         TEXT NOT NULL,
            date         TEXT NOT NULL,
            open         REAL NOT NULL,
            high         REAL NOT NULL,
            low          REAL NOT NULL,
            close        REAL NOT NULL,
            volume       INTEGER NOT NULL,
            amount       REAL NOT NULL,
            change_pct   REAL NOT NULL,
            turnover_rate REAL NOT NULL,
            PRIMARY KEY (code, date)
        )
    """,
    "lhb_details": """
        CREATE TABLE IF NOT EXISTS lhb_details (
            code             TEXT NOT NULL,
            name             TEXT NOT NULL,
            date             TEXT NOT NULL,
            close            REAL NOT NULL,
            change_pct       REAL NOT NULL,
            net_buy_amount   REAL NOT NULL,
            buy_amount       REAL NOT NULL,
            sell_amount      REAL NOT NULL,
            total_amount     REAL NOT NULL,
            reason           TEXT NOT NULL,
            turnover_rate    REAL NOT NULL,
            PRIMARY KEY (code, date)
        )
    """,
    "fund_flows": """
        CREATE TABLE IF NOT EXISTS fund_flows (
            code                  TEXT NOT NULL,
            name                  TEXT NOT NULL,
            date                  TEXT NOT NULL,
            main_net_inflow       REAL NOT NULL,
            retail_net_inflow     REAL NOT NULL,
            main_net_inflow_pct   REAL NOT NULL,
            PRIMARY KEY (code, date)
        )
    """,
    "north_funds": """
        CREATE TABLE IF NOT EXISTS north_funds (
            date               TEXT NOT NULL PRIMARY KEY,
            sh_net_inflow      REAL NOT NULL,
            sz_net_inflow      REAL NOT NULL,
            total_net_inflow   REAL NOT NULL
        )
    """,
    "board_daily": """
        CREATE TABLE IF NOT EXISTS board_daily (
            board_name   TEXT NOT NULL,
            board_type   TEXT NOT NULL,
            date         TEXT NOT NULL,
            change_pct   REAL NOT NULL,
            up_count     INTEGER NOT NULL,
            down_count   INTEGER NOT NULL,
            leader_code  TEXT DEFAULT '',
            leader_name  TEXT DEFAULT '',
            PRIMARY KEY (board_name, board_type, date)
        )
    """,
    "policies": """
        CREATE TABLE IF NOT EXISTS policies (
            url            TEXT NOT NULL PRIMARY KEY,
            title          TEXT NOT NULL,
            publish_date   TEXT NOT NULL,
            source         TEXT NOT NULL,
            summary        TEXT DEFAULT '',
            keywords       TEXT DEFAULT ''
        )
    """,
    "research_reports": """
        CREATE TABLE IF NOT EXISTS research_reports (
            url            TEXT NOT NULL PRIMARY KEY,
            title          TEXT NOT NULL,
            stock_code     TEXT NOT NULL,
            stock_name     TEXT NOT NULL,
            institution    TEXT NOT NULL,
            publish_date   TEXT NOT NULL,
            summary        TEXT DEFAULT '',
            rating         TEXT DEFAULT '',
            keywords       TEXT DEFAULT ''
        )
    """,
    "financial_reports": """
        CREATE TABLE IF NOT EXISTS financial_reports (
            code                TEXT NOT NULL,
            name                TEXT NOT NULL,
            report_date         TEXT NOT NULL,
            report_type         TEXT NOT NULL,
            revenue             REAL DEFAULT 0,
            net_profit          REAL DEFAULT 0,
            total_assets        REAL DEFAULT 0,
            total_liabilities   REAL DEFAULT 0,
            equity              REAL DEFAULT 0,
            roe                 REAL DEFAULT 0,
            gross_margin        REAL DEFAULT 0,
            PRIMARY KEY (code, report_date)
        )
    """,
    "data_meta": """
        CREATE TABLE IF NOT EXISTS data_meta (
            table_name   TEXT NOT NULL,
            code         TEXT NOT NULL,
            latest_date  TEXT NOT NULL,
            PRIMARY KEY (table_name, code)
        )
    """,
}


def init_database() -> None:
    """初始化数据库：创建所有表。"""
    conn = get_connection()
    for table_name, ddl in CREATE_TABLE_SQL.items():
        conn.execute(ddl)
    conn.commit()
