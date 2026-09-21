"""
Postgres connection pool (psycopg3). This is the ONLY module that touches
`vector` columns directly, via raw SQL -- decision-api never maps them in
JPA, and gets similarity results by calling ml-service instead.
"""
from psycopg_pool import ConnectionPool

from app.config import settings

pool = ConnectionPool(settings.database_url, min_size=1, max_size=5, open=True)


def get_conn():
    return pool.connection()
