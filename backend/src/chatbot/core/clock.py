"""统一的时间格式：UTC 的 ISO 8601 字符串。

精确到秒、带 +00:00 后缀，按字典序排序即等于按时间排序；
SQLite 里以 TEXT 存储，读写都不需要额外转换。
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """返回当前 UTC 时间（秒级精度）。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
