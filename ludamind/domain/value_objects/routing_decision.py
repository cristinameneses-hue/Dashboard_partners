"""
Routing Decision Value Object

Represents the decision of which database to route a query to.
This encapsulates the routing logic results and provides confidence metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .database_type import DatabaseType


@dataclass(frozen=True)
class RoutingDecision:
    """
    Immutable value object representing a database routing decision.

    This object contains the routing decision along with the reasoning
    and confidence scores that led to the decision.
    """

    # Core decision
    primary_database: DatabaseType  # The selected database
    confidence: float  # Confidence score (0.0 to 1.0)

    # Reasoning data
    keyword_scores: Dict[DatabaseType, int]  # Keyword match scores per database
    matched_keywords: Dict[DatabaseType, List[str]]  # Which keywords matched
    reasoning: str  # Human-readable explanation of the decision

    # Alternative options
    alternative_database: Optional[DatabaseType] = None  # Second choice if any
    alternative_confidence: Optional[float] = None  # Confidence for alternative

    # Metadata
    requires_join: bool = False  # Whether query needs data from multiple databases
    is_ambiguous: bool = False  # Whether the routing decision is ambiguous

    def __post_init__(self):
        """
        Validate the routing decision upon creation.

        Raises:
            ValueError: If validation fails
        """
        # Validate confidence score
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

        # Validate alternative confidence if provided
        if self.alternative_confidence is not None:
            if not 0.0 <= self.alternative_confidence <= 1.0:
                raise ValueError(
                    f"Alternative confidence must be between 0 and 1, "
                    f"got {self.alternative_confidence}"
                )

        # Check if ambiguous based on confidence scores
        if self.alternative_confidence is not None:
            confidence_diff = self.confidence - self.alternative_confidence
            if confidence_diff < 0.2:  # Less than 20% difference
                object.__setattr__(self, 'is_ambiguous', True)

    @property
    def is_high_confidence(self) -> bool:
        """
        Check if this is a high confidence routing decision.

        Returns:
            True if confidence >= 0.8
        """
        return self.confidence >= 0.8

    @property
    def is_low_confidence(self) -> bool:
        """
        Check if this is a low confidence routing decision.

        Returns:
            True if confidence < 0.5
        """
        return self.confidence < 0.5

    @property
    def needs_confirmation(self) -> bool:
        """
        Check if this routing decision should be confirmed with the user.

        Returns:
            True if low confidence or ambiguous
        """
        return self.is_low_confidence or self.is_ambiguous

    @property
    def total_keywords_matched(self) -> int:
        """
        Get the total number of keywords matched across all databases.

        Returns:
            Total keyword match count
        """
        return sum(self.keyword_scores.values())

    def get_confidence_level(self) -> str:
        """
        Get a human-readable confidence level.

        Returns:
            Confidence level string
        """
        if self.confidence >= 0.9:
            return "Very High"
        elif self.confidence >= 0.7:
            return "High"
        elif self.confidence >= 0.5:
            return "Medium"
        elif self.confidence >= 0.3:
            return "Low"
        else:
            return "Very Low"

    def get_recommendation(self) -> str:
        """
        Get a recommendation based on the routing decision.

        Returns:
            Recommendation string
        """
        if self.requires_join:
            return (
                f"Query requires data from multiple databases. "
                f"Primary: {self.primary_database.get_display_name()}"
            )

        if self.is_high_confidence:
            return f"Use {self.primary_database.get_display_name()} (High confidence: {self.confidence:.1%})"

        if self.is_ambiguous:
            return (
                f"Ambiguous query. Suggest {self.primary_database.get_display_name()} "
                f"({self.confidence:.1%}) but {self.alternative_database.get_display_name()} "
                f"({self.alternative_confidence:.1%}) is also possible"
            )

        if self.is_low_confidence:
            return (
                f"Low confidence routing to {self.primary_database.get_display_name()}. "
                f"Consider clarifying the query."
            )

        return f"Use {self.primary_database.get_display_name()} (Confidence: {self.confidence:.1%})"

    def to_dict(self) -> Dict[str, any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'primary_database': self.primary_database.value,
            'confidence': self.confidence,
            'confidence_level': self.get_confidence_level(),
            'keyword_scores': {k.value: v for k, v in self.keyword_scores.items()},
            'matched_keywords': {k.value: v for k, v in self.matched_keywords.items()},
            'reasoning': self.reasoning,
            'alternative_database': self.alternative_database.value if self.alternative_database else None,
            'alternative_confidence': self.alternative_confidence,
            'requires_join': self.requires_join,
            'is_ambiguous': self.is_ambiguous,
            'needs_confirmation': self.needs_confirmation,
            'recommendation': self.get_recommendation()
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Route to {self.primary_database.value} "
            f"(confidence: {self.confidence:.1%})"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"RoutingDecision(database={self.primary_database.value}, "
            f"confidence={self.confidence:.2f}, "
            f"ambiguous={self.is_ambiguous})"
        )