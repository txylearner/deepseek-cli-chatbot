"""SQLite 连接的统一入口。

每个操作开一个短连接：SQLite 打开文件几乎没有成本，
这样不需要处理跨线程共享连接的问题；写入由数据库自己的锁保证串行。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_TIMEOUT_SECONDS = 5.0


def utc_now_iso() -> str:
    """统一的时间格式：UTC 的 ISO 8601 字符串，按字典序即可排序。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def open_connection(db_path: str | Path) -> sqlite3.Connection:
    """打开连接并设置好本项目需要的 PRAGMA。"""
    connection = sqlite3.connect(str(db_path), timeout=DB_TIMEOUT_SECONDS)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


@contextmanager
def transaction(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """一个事务：正常结束自动提交，抛异常自动回滚，最后关闭连接。"""
    connection = open_connection(db_path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()
