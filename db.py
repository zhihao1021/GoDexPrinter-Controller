from psycopg2.pool import SimpleConnectionPool
from psycopg2.extensions import connection, cursor

from contextlib import contextmanager
from os.path import abspath
from typing import Generator, Optional

from config import (
    DB_NAME,
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_SSLMODE,
    DB_SSLROOTCERT,
    DB_MINCONN,
    DB_MAXCONN
)

pool: Optional[SimpleConnectionPool] = None


@contextmanager
def get_cursor() -> Generator[cursor, None, None]:
    global pool
    if pool is None:
        pool = SimpleConnectionPool(
            minconn=DB_MINCONN,
            maxconn=DB_MAXCONN,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode=DB_SSLMODE,
            sslrootcert=abspath(DB_SSLROOTCERT) if DB_SSLROOTCERT else None
        )
    conn: connection = pool.getconn()

    try:
        with conn.cursor() as cursor:
            yield cursor
    finally:
        pool.putconn(conn)
