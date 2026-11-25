import os
import threading
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from . import config

_trava = threading.Lock()
_pool = None
_pid = None


def _criar_pool():
    informacao = (
        f"host={config.DB_HOST} port={config.DB_PORT} dbname={config.DB_NAME} "
        f"user={config.DB_USER} password={config.DB_PASSWORD}"
    )
    pool = ConnectionPool(
        informacao,
        min_size=config.POOL_SIZE,
        max_size=config.POOL_SIZE,
        kwargs={"autocommit": True, "row_factory": dict_row},
        timeout=10,
        open=False,
    )
    pool.open(wait=True, timeout=30)
    return pool


def pool():
    global _pool, _pid
    if _pool is None or _pid != os.getpid():
        with _trava:
            if _pool is None or _pid != os.getpid():
                _pool = _criar_pool()
                _pid = os.getpid()
    return _pool


@contextmanager
def conexao():
    with pool().connection() as c:
        yield c