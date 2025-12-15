"""
Validation result data structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevel(Enum):
    """Risk level of a query."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """
    Result of query validation.

    Attributes:
        is_safe: Whether query is safe to execute
        risk_level: Risk level of the query
        blocked_reasons: List of reasons why query was blocked
        warnings: Non-blocking warnings
        sanitized_query: Sanitized version of query (if applicable)
    """
    is_safe: bool
    risk_level: RiskLevel
    blocked_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_query: Optional[str] = None

    @classmethod
    def safe(cls, warnings: Optional[List[str]] = None) -> 'ValidationResult':
        """Create a safe validation result."""
        return cls(
            is_safe=True,
            risk_level=RiskLevel.SAFE,
            warnings=warnings or []
        )

    @classmethod
    def blocked(cls, reasons: List[str], risk_level: RiskLevel = RiskLevel.CRITICAL) -> 'ValidationResult':
        """Create a blocked validation result."""
        return cls(
            is_safe=False,
            risk_level=risk_level,
            blocked_reasons=reasons
        )

    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.is_safe
