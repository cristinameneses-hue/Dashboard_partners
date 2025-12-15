"""
Database Type Value Object

Represents the type of database in the system.
This enumeration ensures type safety and prevents invalid database types.
"""

from enum import Enum


class DatabaseType(str, Enum):
    """
    Enumeration of supported database types.

    This value object ensures that only valid database types are used
    throughout the application, preventing typos and invalid values.
    """

    MYSQL = "mysql"
    MONGODB = "mongodb"

    @classmethod
    def from_string(cls, value: str) -> 'DatabaseType':
        """
        Create DatabaseType from string value.

        Args:
            value: String representation of database type

        Returns:
            DatabaseType enum value

        Raises:
            ValueError: If value is not a valid database type
        """
        value_lower = value.lower().strip()

        if value_lower in ['mysql', 'sql', 'relational']:
            return cls.MYSQL
        elif value_lower in ['mongodb', 'mongo', 'nosql']:
            return cls.MONGODB
        else:
            raise ValueError(f"Invalid database type: {value}. Must be 'mysql' or 'mongodb'")

    def get_display_name(self) -> str:
        """
        Get human-readable display name for the database type.

        Returns:
            Display name string
        """
        return {
            DatabaseType.MYSQL: "MySQL (Analytics)",
            DatabaseType.MONGODB: "MongoDB (Operations)"
        }[self]

    def get_default_port(self) -> int:
        """
        Get the default port for this database type.

        Returns:
            Default port number
        """
        return {
            DatabaseType.MYSQL: 3306,
            DatabaseType.MONGODB: 27017
        }[self]

    def supports_transactions(self) -> bool:
        """
        Check if this database type supports transactions.

        Returns:
            True if transactions are supported
        """
        return {
            DatabaseType.MYSQL: True,
            DatabaseType.MONGODB: True  # MongoDB 4.0+ supports transactions
        }[self]

    def supports_sql(self) -> bool:
        """
        Check if this database type supports SQL queries.

        Returns:
            True if SQL is supported
        """
        return self == DatabaseType.MYSQL

    def __str__(self) -> str:
        """String representation."""
        return self.value