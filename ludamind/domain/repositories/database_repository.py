"""
Database Repository Interface

This module defines the abstract interface for database operations.
All concrete database implementations (MySQL, MongoDB, etc.) must implement this interface.

Following SOLID principles:
- Single Responsibility: Only defines database operation contracts
- Open/Closed: Can be extended with new implementations without modification
- Dependency Inversion: Domain depends on this abstraction, not concrete classes
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class DatabaseRepository(ABC):
    """
    Abstract repository for database operations.

    This interface defines the contract that all database implementations must follow.
    It ensures that the domain layer can work with any database without knowing
    the specific implementation details.
    """

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a database query.

        Args:
            query: The query to execute (SQL for MySQL, MongoDB query for MongoDB)
            params: Optional parameters for the query
            timeout: Optional timeout in seconds

        Returns:
            List of dictionaries representing the query results

        Raises:
            DatabaseConnectionError: If connection fails
            QueryExecutionError: If query execution fails
            TimeoutError: If query exceeds timeout
        """
        pass

    @abstractmethod
    async def execute_aggregation(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]],
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute an aggregation pipeline (MongoDB specific, but can be adapted).

        Args:
            collection: The collection/table name
            pipeline: Aggregation pipeline stages
            timeout: Optional timeout in seconds

        Returns:
            List of aggregated results

        Raises:
            NotImplementedError: If database doesn't support aggregation
            QueryExecutionError: If aggregation fails
        """
        pass

    @abstractmethod
    async def count(
        self,
        collection_or_table: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count documents/rows in a collection/table.

        Args:
            collection_or_table: The collection or table name
            filter_conditions: Optional filter conditions

        Returns:
            Count of matching documents/rows
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if the database connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.

        Returns:
            Dictionary containing database information:
            - name: Database name
            - type: Database type (mysql, mongodb, etc.)
            - version: Database version
            - size: Database size (if available)
            - tables_or_collections: List of table/collection names
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the database connection.

        This method should properly close all connections and clean up resources.
        """
        pass

    @abstractmethod
    async def begin_transaction(self) -> Any:
        """
        Begin a database transaction.

        Returns:
            Transaction object or context

        Note:
            Not all databases support transactions (e.g., some NoSQL databases).
            Implementations should handle this appropriately.
        """
        pass

    @abstractmethod
    async def commit_transaction(self, transaction: Any) -> None:
        """
        Commit a database transaction.

        Args:
            transaction: The transaction object to commit
        """
        pass

    @abstractmethod
    async def rollback_transaction(self, transaction: Any) -> None:
        """
        Rollback a database transaction.

        Args:
            transaction: The transaction object to rollback
        """
        pass

    @property
    @abstractmethod
    def database_type(self) -> str:
        """
        Get the type of database.

        Returns:
            String identifier for the database type ('mysql', 'mongodb', etc.)
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the repository is currently connected to the database.

        Returns:
            True if connected, False otherwise
        """
        pass