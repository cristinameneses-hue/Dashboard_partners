"""
MySQL Repository Implementation

Concrete implementation of DatabaseRepository for MySQL databases.
Follows SOLID principles with proper separation of concerns.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager
import aiomysql
from aiomysql import DictCursor, Pool
import json

from domain.repositories import DatabaseRepository
from domain.value_objects import DatabaseType, QueryResult


logger = logging.getLogger(__name__)


class MySQLRepository(DatabaseRepository):
    """
    MySQL repository implementation.

    This class implements the DatabaseRepository interface for MySQL databases,
    providing connection pooling, query execution, and proper error handling.
    """

    def __init__(self,
                 host: str = "localhost",
                 port: int = 3306,
                 database: str = "",
                 username: str = "",
                 password: str = "",
                 pool_size: int = 10,
                 max_overflow: int = 5,
                 connection_timeout: int = 30,
                 query_timeout: int = 60,
                 read_only: bool = True):
        """
        Initialize MySQL repository.

        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            connection_timeout: Connection timeout in seconds
            query_timeout: Query timeout in seconds
            read_only: Whether to enforce read-only mode
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.connection_timeout = connection_timeout
        self.query_timeout = query_timeout
        self.read_only = read_only

        self._pool: Optional[Pool] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish connection to the database.

        Creates a connection pool for efficient connection management.
        """
        if self._connected:
            logger.warning("Already connected to MySQL database")
            return

        try:
            self._pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                db=self.database,
                minsize=1,
                maxsize=self.pool_size,
                connect_timeout=self.connection_timeout,
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=True
            )
            self._connected = True
            logger.info(f"Connected to MySQL database: {self.database}")

        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise ConnectionError(f"MySQL connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """
        Close database connection.

        Properly closes the connection pool and releases resources.
        """
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._connected = False
            logger.info(f"Disconnected from MySQL database: {self.database}")

    async def execute_query(self,
                           query: str,
                           params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a database query.

        Args:
            query: SQL query to execute
            params: Query parameters for parameterized queries

        Returns:
            List of result dictionaries

        Raises:
            ValueError: If query violates read-only mode
            ConnectionError: If not connected
            RuntimeError: If query execution fails
        """
        if not self._connected:
            await self.connect()

        # Validate query in read-only mode
        if self.read_only and self._is_write_query(query):
            raise ValueError("Write operations are not allowed in read-only mode")

        try:
            async with self._get_connection() as conn:
                async with conn.cursor(DictCursor) as cursor:
                    # Set query timeout
                    await cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={self.query_timeout * 1000}")

                    # Execute query with parameters
                    if params:
                        await cursor.execute(query, params)
                    else:
                        await cursor.execute(query)

                    # Fetch results
                    if cursor.description:
                        results = await cursor.fetchall()
                        return [dict(row) for row in results]
                    else:
                        # For queries without results (INSERT, UPDATE, etc.)
                        return [{
                            'affected_rows': cursor.rowcount,
                            'last_insert_id': cursor.lastrowid
                        }]

        except asyncio.TimeoutError:
            raise RuntimeError(f"Query timeout after {self.query_timeout} seconds")
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise RuntimeError(f"Query execution failed: {str(e)}")

    async def execute_transaction(self,
                                 queries: List[Tuple[str, Optional[Dict[str, Any]]]]) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in a transaction.

        Args:
            queries: List of (query, params) tuples

        Returns:
            List of results for each query

        Raises:
            ValueError: If any query violates read-only mode
            RuntimeError: If transaction fails
        """
        if self.read_only:
            raise ValueError("Transactions are not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        results = []
        async with self._get_connection() as conn:
            try:
                await conn.begin()

                async with conn.cursor(DictCursor) as cursor:
                    for query, params in queries:
                        if params:
                            await cursor.execute(query, params)
                        else:
                            await cursor.execute(query)

                        if cursor.description:
                            result = await cursor.fetchall()
                            results.append([dict(row) for row in result])
                        else:
                            results.append([{
                                'affected_rows': cursor.rowcount,
                                'last_insert_id': cursor.lastrowid
                            }])

                await conn.commit()
                return results

            except Exception as e:
                await conn.rollback()
                logger.error(f"Transaction failed: {str(e)}")
                raise RuntimeError(f"Transaction failed: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is successful
        """
        try:
            if not self._connected:
                await self.connect()

            async with self._get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result == (1,)

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of column definitions
        """
        query = """
        SELECT
            COLUMN_NAME as name,
            DATA_TYPE as type,
            IS_NULLABLE as nullable,
            COLUMN_DEFAULT as default_value,
            CHARACTER_MAXIMUM_LENGTH as max_length,
            COLUMN_KEY as key_type,
            EXTRA as extra
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """

        return await self.execute_query(query, (self.database, table_name))

    async def list_tables(self) -> List[str]:
        """
        List all tables in the database.

        Returns:
            List of table names
        """
        query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
        """

        results = await self.execute_query(query, (self.database,))
        return [row['TABLE_NAME'] for row in results]

    async def get_database_size(self) -> float:
        """
        Get database size in MB.

        Returns:
            Database size in megabytes
        """
        query = """
        SELECT
            SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024 as size_mb
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
        """

        result = await self.execute_query(query, (self.database,))
        return float(result[0]['size_mb']) if result and result[0]['size_mb'] else 0.0

    async def get_table_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        # Use approximate count for performance
        query = """
        SELECT TABLE_ROWS as count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """

        result = await self.execute_query(query, (self.database, table_name))
        if result and result[0]['count'] is not None:
            return int(result[0]['count'])

        # Fall back to exact count if approximate is not available
        query = f"SELECT COUNT(*) as count FROM `{table_name}`"
        result = await self.execute_query(query)
        return int(result[0]['count']) if result else 0

    async def explain_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get execution plan for a query.

        Args:
            query: SQL query to explain
            params: Query parameters

        Returns:
            Execution plan details
        """
        explain_query = f"EXPLAIN {query}"
        return await self.execute_query(explain_query, params)

    @asynccontextmanager
    async def _get_connection(self):
        """
        Get a connection from the pool.

        Context manager that ensures proper connection handling.
        """
        if not self._pool:
            raise ConnectionError("Not connected to database")

        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            self._pool.release(conn)

    def _is_write_query(self, query: str) -> bool:
        """
        Check if query is a write operation.

        Args:
            query: SQL query to check

        Returns:
            True if query is a write operation
        """
        query_upper = query.strip().upper()
        write_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER',
            'DROP', 'TRUNCATE', 'REPLACE', 'MERGE'
        ]

        return any(query_upper.startswith(keyword) for keyword in write_keywords)

    @property
    def database_type(self) -> DatabaseType:
        """Get the database type."""
        return DatabaseType.MYSQL

    async def create_result(self,
                           data: List[Dict[str, Any]],
                           query: str,
                           execution_time_ms: float) -> QueryResult:
        """
        Create a QueryResult object.

        Args:
            data: Query result data
            query: Executed query
            execution_time_ms: Query execution time

        Returns:
            QueryResult value object
        """
        return QueryResult(
            data=data,
            count=len(data),
            is_success=True,
            error_message=None,
            execution_time_ms=execution_time_ms,
            database_type=self.database_type,
            query_executed=query
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"MySQLRepository(host='{self.host}', port={self.port}, database='{self.database}')"