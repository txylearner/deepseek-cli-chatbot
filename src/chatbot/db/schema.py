"""建表入口：表结构由 ORM 模型声明，这里只负责“缺什么建什么”。

create_all(checkfirst=True) 只检查表是否存在：

    表已存在 -> 一条 DDL 都不发，旧数据原样保留；
    表不存在 -> 按 db/models.py 的声明建表。

所以从第 4 次作业的裸 SQL 升级到 ORM，不会删表、不会清库。
"""

from __future__ import annotations

from pathlib import Path

from .engine import get_engine
from .models import Base


def init_schema(db_path: str | Path) -> None:
    """确保表存在；可重复执行，不会改动已有数据。"""
    path = str(db_path)
    if path != ":memory:":
        Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(get_engine(path))
