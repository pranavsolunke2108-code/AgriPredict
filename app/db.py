"""AgriPredict Database Connection and Query Helpers.

Provides a thread-safe connection pool using mysql-connector-python
and helper functions to execute parameterized SQL queries cleanly.
"""

import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union
import mysql.connector
from mysql.connector import errorcode
from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

from app.config import settings

logger = logging.getLogger("agripredict.db")

# Global pool reference (lazily initialized)
_pool: Optional[MySQLConnectionPool] = None
_custom_connection_provider: Optional[Callable[[], Any]] = None


def get_connection_pool() -> MySQLConnectionPool:
    """Initialize or return the existing MySQL connection pool."""
    global _pool
    if _pool is None:
        try:
            logger.info("Initializing MySQL connection pool: %s", settings.DB_POOL_NAME)
            _pool = MySQLConnectionPool(
                pool_name=settings.DB_POOL_NAME,
                pool_size=settings.DB_POOL_SIZE,
                pool_reset_session=True,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
            )
        except mysql.connector.Error as err:
            logger.error("Failed to connect to MySQL database '%s': %s", settings.DB_NAME, err)
            raise RuntimeError(
                f"Database connection error: Could not connect to MySQL database '{settings.DB_NAME}' "
                f"on {settings.DB_HOST}:{settings.DB_PORT}. Please verify your .env credentials."
            ) from err
    return _pool


def set_connection_provider(provider: Optional[Callable[[], Any]]) -> None:
    """Set a custom connection provider (used for test isolation/mocking)."""
    global _custom_connection_provider
    _custom_connection_provider = provider


def get_connection():
    """Retrieve a database connection from the pool or test provider."""
    if _custom_connection_provider is not None:
        return _custom_connection_provider()
    pool = get_connection_pool()
    return pool.get_connection()


def get_migration_connection():
    """Retrieve a database connection using the migration/DDL account (agripredict_migrate)."""
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_MIGRATE_USER,
        password=settings.DB_MIGRATE_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


@contextmanager
def get_db_cursor(
    commit: bool = False,
    dictionary: bool = True
) -> Generator[Any, None, None]:
    """Context manager providing a database cursor.

    Automatically handles connection release, committing transactions,
    and rolling back on unhandled errors.

    Args:
        commit: If True, commits the transaction before exiting.
        dictionary: If True, yields a dictionary cursor where columns are keys.
    """
    conn = get_connection()
    try:
        # Check if connector supports dictionary parameter
        try:
            cursor = conn.cursor(dictionary=dictionary)
        except TypeError:
            cursor = conn.cursor()

        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            if commit:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            cursor.close()
    finally:
        conn.close()


def fetch_one(
    query: str,
    params: Optional[Union[Tuple, List, dict]] = None,
    dictionary: bool = True
) -> Optional[Any]:
    """Execute a parameterized SELECT query and fetch a single record.

    Args:
        query: SQL query containing '%s' parameter placeholders.
        params: Tuple/list of values to safely bind.
        dictionary: Return record as dict if True, else tuple.
    """
    with get_db_cursor(commit=False, dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def fetch_all(
    query: str,
    params: Optional[Union[Tuple, List, dict]] = None,
    dictionary: bool = True
) -> List[Any]:
    """Execute a parameterized SELECT query and fetch all matching records.

    Args:
        query: SQL query containing '%s' parameter placeholders.
        params: Tuple/list of values to safely bind.
        dictionary: Return records as list of dicts if True.
    """
    with get_db_cursor(commit=False, dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def execute_query(
    query: str,
    params: Optional[Union[Tuple, List, dict]] = None,
    commit: bool = True
) -> Tuple[int, int]:
    """Execute a parameterized INSERT, UPDATE, or DELETE query.

    Args:
        query: SQL query containing '%s' parameter placeholders.
        params: Tuple/list of values to safely bind.
        commit: Whether to commit transaction immediately.

    Returns:
        Tuple of (lastrowid, rowcount)
    """
    with get_db_cursor(commit=commit) as cursor:
        cursor.execute(query, params or ())
        last_id = getattr(cursor, "lastrowid", 0) or 0
        row_count = getattr(cursor, "rowcount", 0) or 0
        return last_id, row_count


def execute_insert(
    query: str,
    params: Optional[Union[Tuple, List, dict]] = None
) -> int:
    """Execute an INSERT query and return the generated AUTO_INCREMENT primary key."""
    last_id, _ = execute_query(query, params, commit=True)
    return last_id


def execute_update(
    query: str,
    params: Optional[Union[Tuple, List, dict]] = None
) -> int:
    """Execute an UPDATE or DELETE query and return the number of affected rows."""
    _, row_count = execute_query(query, params, commit=True)
    return row_count


@contextmanager
def get_admin_cursor(
    admin_farmer_id: int,
    commit: bool = True,
    dictionary: bool = True
) -> Generator[Any, None, None]:
    """Context manager providing a database cursor for admin operations.

    Executes `SET @app_user = CONCAT('admin:', admin_farmer_id)` on the
    connection before yielding the cursor, ensuring MySQL audit triggers
    record the executing admin ID.
    """
    conn = get_connection()
    try:
        try:
            cursor = conn.cursor(dictionary=dictionary)
        except TypeError:
            cursor = conn.cursor()

        try:
            user_val = f"admin:{admin_farmer_id}"
            cursor.execute("SET @app_user = %s", (user_val,))
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            if commit:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            cursor.close()
    finally:
        conn.close()


def execute_admin_query(
    query: str,
    params: Optional[Union[Tuple, List, dict]] = None,
    admin_farmer_id: int = 0,
    commit: bool = True
) -> Tuple[int, int]:
    """Execute an admin write query (INSERT/UPDATE/DELETE) with session @app_user set."""
    with get_admin_cursor(admin_farmer_id=admin_farmer_id, commit=commit) as cursor:
        cursor.execute(query, params or ())
        last_id = getattr(cursor, "lastrowid", 0) or 0
        row_count = getattr(cursor, "rowcount", 0) or 0
        return last_id, row_count


class DatabaseProcedureError(Exception):
    """Exception raised when a stored procedure raises a SQLSTATE error (e.g. 45000)."""

    def __init__(self, message: str, sqlstate: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.sqlstate = sqlstate


def call_procedure(
    proc_name: str,
    params: Optional[Union[Tuple, List]] = None
) -> List[Dict[str, Any]]:
    """Execute a stored procedure and return result set as a list of dicts.

    Properly drains multiple result sets to prevent 'Commands out of sync' errors.
    Translates MySQL SQLSTATE 45000 errors into DatabaseProcedureError.
    """
    if _custom_connection_provider is not None:
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            try:
                if hasattr(cursor, "callproc"):
                    return cursor.callproc(proc_name, params or ())
                placeholders = ", ".join(["%s"] * len(params or ()))
                cursor.execute(f"CALL {proc_name}({placeholders})", params or ())
                return cursor.fetchall()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        finally:
            conn.close()

    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            placeholders = ", ".join(["%s"] * len(params or ()))
            call_query = f"CALL {proc_name}({placeholders})"
            cursor.execute(call_query, params or ())

            results = []
            try:
                results = cursor.fetchall()
            except Exception:
                pass

            # Drain any subsequent result sets
            try:
                while cursor.nextset():
                    more = cursor.fetchall()
                    if not results and more:
                        results = more
            except Exception:
                pass

            conn.commit()
            return results
        except mysql.connector.Error as err:
            try:
                conn.rollback()
            except Exception:
                pass
            sqlstate = getattr(err, "sqlstate", None)
            raise DatabaseProcedureError(err.msg, sqlstate=sqlstate) from err
        finally:
            try:
                cursor.close()
            except Exception:
                pass
    finally:
        conn.close()

