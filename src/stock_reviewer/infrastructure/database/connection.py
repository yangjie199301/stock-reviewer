"""SQLite 连接管理。

提供数据库连接的获取和生命周期管理。
"""

import sqlite3
from pathlib import Path
from typing import Optional

from stock_reviewer.core.config import settings


_connection: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（单例，惰性初始化）。

    Returns:
        SQLite 连接对象。
    """
    global _connection
    if _connection is None:
        db_path = Path(settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(db_path))
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def close_connection() -> None:
    """关闭数据库连接。"""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
