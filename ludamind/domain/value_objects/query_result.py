"""
Query Result Value Object

Represents the result of a database query execution.
This is an immutable container for query results with metadata.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass(frozen=True)
class QueryResult:
    """
    Immutable value object representing query execution results.

    This object contains not just the data but also metadata about
    the query execution for tracking and optimization purposes.
    """

    # Core data
    data: List[Dict[str, Any]]  # The actual query results
    count: int  # Number of results returned
    total_count: Optional[int]  # Total count if different from returned (e.g., with LIMIT)

    # Execution metadata
    execution_time_ms: float  # Query execution time in milliseconds
    database_type: str  # Which database was queried
    query_executed: str  # The actual query that was executed

    # Optional metadata
    cached: bool = False  # Whether result was from cache
    cache_key: Optional[str] = None  # Cache key if cached
    error: Optional[str] = None  # Error message if any
    warnings: List[str] = field(default_factory=list)  # Any warnings

    # Timestamp
    executed_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """
        Validate the query result upon creation.

        Raises:
            ValueError: If validation fails
        """
        # Validate that count matches data length
        if self.count != len(self.data):
            # Use object.__setattr__ to modify frozen dataclass
            object.__setattr__(self, 'count', len(self.data))

        # Validate execution time
        if self.execution_time_ms < 0:
            raise ValueError("Execution time cannot be negative")

        # Validate total_count if provided
        if self.total_count is not None and self.total_count < self.count:
            raise ValueError("Total count cannot be less than returned count")

    @property
    def is_success(self) -> bool:
        """
        Check if the query executed successfully.

        Returns:
            True if no error, False otherwise
        """
        return self.error is None

    @property
    def is_empty(self) -> bool:
        """
        Check if the result set is empty.

        Returns:
            True if no results, False otherwise
        """
        return self.count == 0

    @property
    def has_warnings(self) -> bool:
        """
        Check if there are any warnings.

        Returns:
            True if warnings exist, False otherwise
        """
        return len(self.warnings) > 0

    @property
    def was_limited(self) -> bool:
        """
        Check if the results were limited (not all results returned).

        Returns:
            True if total_count > count, False otherwise
        """
        return self.total_count is not None and self.total_count > self.count

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the query result to a dictionary for serialization.

        Returns:
            Dictionary representation of the query result
        """
        return {
            'data': self.data,
            'count': self.count,
            'total_count': self.total_count,
            'execution_time_ms': self.execution_time_ms,
            'database_type': self.database_type,
            'query_executed': self.query_executed,
            'cached': self.cached,
            'cache_key': self.cache_key,
            'error': self.error,
            'warnings': self.warnings,
            'executed_at': self.executed_at.isoformat(),
            'is_success': self.is_success,
            'is_empty': self.is_empty,
            'was_limited': self.was_limited
        }

    def get_summary(self) -> str:
        """
        Get a human-readable summary of the query result.

        Returns:
            Summary string
        """
        if self.error:
            return f"Query failed: {self.error}"

        cache_info = " (cached)" if self.cached else ""
        limit_info = f" (limited from {self.total_count})" if self.was_limited else ""

        return (
            f"Query returned {self.count} results{limit_info} "
            f"in {self.execution_time_ms:.2f}ms{cache_info}"
        )

    def __str__(self) -> str:
        """String representation."""
        return self.get_summary()

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"QueryResult(count={self.count}, "
            f"execution_time={self.execution_time_ms}ms, "
            f"database='{self.database_type}', "
            f"cached={self.cached})"
        )