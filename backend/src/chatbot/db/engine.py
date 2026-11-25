"""引擎与 Session 工厂：数据库访问的唯一入口。

三条约定：

1. 一个数据库文件对应一个 Engine（按绝对路径缓存），连接池在进程内复用；
2. 每次操作从 sessionmaker 取一个新 Session，用完一定关闭；
3. 外键开关与忙等超时通过 connect 事件挂到每条连接上，保证 ON DELETE CASCADE 真的生效。

路由都是同步 def，FastAPI 会把它们丢进线程池执行，所以这里用同步 Session。
不要把这些阻塞调用放进 async def：那会卡住事件循环（见 README「并发与性能」）。
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

DB_TIMEOUT_SECONDS = 5.0
MAX_CACHED_ENGINES = 8

_ENGINES: dict[str, Engine] = {}
_ENGINES_LOCK = threading.Lock()


def _configure_connection(dbapi_connection: Any, _record: Any) -> None:
    """每条新连接都要设的 PRAGMA：外键约束 + 锁等待上限。

    同时把事务控制权收回到 SQLAlchemy 手里：pysqlite 默认只在 DML 前发 BEGIN，
    会让 SAVEPOINT 变成最外层事务、RELEASE 时被提前提交。关掉它的隐式事务，
    改由下面的 "begin" 事件显式发 BEGIN，嵌套事务（SAVEPOINT）才是真的嵌套。
    """
    dbapi_connection.isolation_level = None  # 关闭 pysqlite 的隐式事务
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.close()


def _begin_transaction(connection: Connection) -> None:
    """显式开启事务，保证提交/回滚真的覆盖整轮对话。"""
    connection.exec_driver_sql("BEGIN")


def _database_key(db_path: str) -> str:
    """缓存键用绝对路径，避免不同工作目录下的同名相对路径串用同一个引擎。"""
    if db_path == ":memory:":
        return db_path
    return str(Path(db_path).resolve())


def _build_engine(db_path: str) -> Engine:
    connect_args: dict[str, Any] = {"timeout": DB_TIMEOUT_SECONDS}
    kwargs: dict[str, Any] = {"connect_args": connect_args}
    if db_path == ":memory:":
        # 内存库只在一个连接里存在，所有线程必须共用同一条连接
        kwargs["poolclass"] = StaticPool
        connect_args["check_same_thread"] = False
        url = "sqlite://"
    else:
        url = "sqlite:///" + Path(db_path).as_posix()
    engine = create_engine(url, **kwargs)
    event.listen(engine, "connect", _configure_connection)
    event.listen(engine, "begin", _begin_transaction)
    return engine


def get_engine(db_path: str) -> Engine:
    """按绝对路径取 Engine，同一个库在进程内只建一次连接池。"""
    key = _database_key(db_path)
    with _ENGINES_LOCK:
        engine = _ENGINES.get(key)
        if engine is None:
            if len(_ENGINES) >= MAX_CACHED_ENGINES:
                _, oldest = _ENGINES.popitem()  # 最早的引擎：dispose 只关连接池，不影响后续使用
                oldest.dispose()
            engine = _build_engine(key)
            _ENGINES[key] = engine
        return engine


def dispose_engine(db_path: str) -> None:
    """关掉某个库的连接池（测试里用来模拟“重启服务”）。"""
    key = _database_key(db_path)
    with _ENGINES_LOCK:
        engine = _ENGINES.pop(key, None)
    if engine is not None:
        engine.dispose()


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Session 工厂：expire_on_commit=False 让返回的对象在关闭后仍可读。"""
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """一个工作单元：正常结束提交，抛异常回滚，无论如何关闭 Session。"""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
