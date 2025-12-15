"""
Time Range Value Object

Represents a time period for queries.
This helps parse and validate temporal expressions in natural language queries.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional, Tuple, Dict
from enum import Enum


class TimeUnit(str, Enum):
    """Enumeration of time units."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass(frozen=True)
class TimeRange:
    """
    Immutable value object representing a time range.

    This object helps parse temporal expressions like "esta semana", "último mes",
    "hoy", "ayer", etc. and convert them to actual date ranges.
    """

    start_date: datetime
    end_date: datetime
    description: str  # Human-readable description
    unit: Optional[TimeUnit] = None  # The time unit if applicable
    is_relative: bool = True  # Whether this is relative (e.g., "last week") or absolute

    def __post_init__(self):
        """
        Validate the time range upon creation.

        Raises:
            ValueError: If validation fails
        """
        if self.start_date > self.end_date:
            raise ValueError(f"Start date ({self.start_date}) cannot be after end date ({self.end_date})")

        # Ensure dates are timezone-aware or both naive
        if self.start_date.tzinfo != self.end_date.tzinfo:
            raise ValueError("Both dates must have the same timezone information")

    @classmethod
    def from_spanish_expression(cls, expression: str, reference_date: Optional[datetime] = None) -> 'TimeRange':
        """
        Create a TimeRange from a Spanish temporal expression.

        Args:
            expression: Spanish expression like "hoy", "esta semana", "último mes"
            reference_date: Reference date for relative expressions (defaults to now)

        Returns:
            TimeRange object

        Raises:
            ValueError: If expression cannot be parsed
        """
        if reference_date is None:
            reference_date = datetime.now()

        expression_lower = expression.lower().strip()

        # Today
        if expression_lower in ['hoy', 'today']:
            start = datetime.combine(reference_date.date(), datetime.min.time())
            end = datetime.combine(reference_date.date(), datetime.max.time())
            return cls(start, end, "Hoy", TimeUnit.DAY, True)

        # Yesterday
        if expression_lower in ['ayer', 'yesterday']:
            yesterday = reference_date.date() - timedelta(days=1)
            start = datetime.combine(yesterday, datetime.min.time())
            end = datetime.combine(yesterday, datetime.max.time())
            return cls(start, end, "Ayer", TimeUnit.DAY, True)

        # This week
        if expression_lower in ['esta semana', 'this week']:
            start = reference_date - timedelta(days=reference_date.weekday())
            start = datetime.combine(start.date(), datetime.min.time())
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            return cls(start, end, "Esta semana", TimeUnit.WEEK, True)

        # Last week
        if expression_lower in ['semana pasada', 'última semana', 'last week']:
            start = reference_date - timedelta(days=reference_date.weekday() + 7)
            start = datetime.combine(start.date(), datetime.min.time())
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            return cls(start, end, "Semana pasada", TimeUnit.WEEK, True)

        # This month
        if expression_lower in ['este mes', 'this month']:
            start = datetime(reference_date.year, reference_date.month, 1)
            # Get last day of month
            if reference_date.month == 12:
                end = datetime(reference_date.year, 12, 31, 23, 59, 59)
            else:
                end = datetime(reference_date.year, reference_date.month + 1, 1) - timedelta(seconds=1)
            return cls(start, end, "Este mes", TimeUnit.MONTH, True)

        # Last month
        if expression_lower in ['mes pasado', 'último mes', 'last month']:
            first_day_this_month = datetime(reference_date.year, reference_date.month, 1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start = datetime(last_day_last_month.year, last_day_last_month.month, 1)
            end = datetime.combine(last_day_last_month, datetime.max.time())
            return cls(start, end, "Mes pasado", TimeUnit.MONTH, True)

        # Last N days
        if 'últimos' in expression_lower and 'días' in expression_lower:
            # Extract number
            import re
            match = re.search(r'últimos (\d+) días', expression_lower)
            if match:
                days = int(match.group(1))
                start = datetime.combine((reference_date - timedelta(days=days-1)).date(), datetime.min.time())
                end = datetime.combine(reference_date.date(), datetime.max.time())
                return cls(start, end, f"Últimos {days} días", TimeUnit.DAY, True)

        # This year
        if expression_lower in ['este año', 'this year']:
            start = datetime(reference_date.year, 1, 1)
            end = datetime(reference_date.year, 12, 31, 23, 59, 59)
            return cls(start, end, "Este año", TimeUnit.YEAR, True)

        # Default to last 7 days if not recognized
        start = datetime.combine((reference_date - timedelta(days=6)).date(), datetime.min.time())
        end = datetime.combine(reference_date.date(), datetime.max.time())
        return cls(start, end, "Últimos 7 días (por defecto)", TimeUnit.DAY, True)

    @property
    def duration_days(self) -> int:
        """
        Get the duration of the time range in days.

        Returns:
            Number of days in the range
        """
        return (self.end_date - self.start_date).days + 1

    @property
    def duration_hours(self) -> float:
        """
        Get the duration of the time range in hours.

        Returns:
            Number of hours in the range
        """
        return (self.end_date - self.start_date).total_seconds() / 3600

    def contains(self, dt: datetime) -> bool:
        """
        Check if a datetime falls within this time range.

        Args:
            dt: Datetime to check

        Returns:
            True if datetime is within range
        """
        return self.start_date <= dt <= self.end_date

    def overlaps(self, other: 'TimeRange') -> bool:
        """
        Check if this time range overlaps with another.

        Args:
            other: Another TimeRange

        Returns:
            True if ranges overlap
        """
        return not (self.end_date < other.start_date or self.start_date > other.end_date)

    def to_sql_condition(self, column_name: str = "date") -> str:
        """
        Convert to SQL WHERE condition.

        Args:
            column_name: Name of the date column

        Returns:
            SQL condition string
        """
        return (
            f"{column_name} >= '{self.start_date.strftime('%Y-%m-%d %H:%M:%S')}' "
            f"AND {column_name} <= '{self.end_date.strftime('%Y-%m-%d %H:%M:%S')}'"
        )

    def to_mongodb_filter(self, field_name: str = "created_at") -> Dict:
        """
        Convert to MongoDB filter condition.

        Args:
            field_name: Name of the date field

        Returns:
            MongoDB filter dictionary
        """
        return {
            field_name: {
                "$gte": self.start_date,
                "$lte": self.end_date
            }
        }

    def to_dict(self) -> Dict[str, any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'description': self.description,
            'unit': self.unit.value if self.unit else None,
            'is_relative': self.is_relative,
            'duration_days': self.duration_days,
            'duration_hours': self.duration_hours
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.description} ({self.start_date.date()} to {self.end_date.date()})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"TimeRange('{self.description}', {self.duration_days} days)"