"""
Query Intent Value Object

Represents the intent or purpose of a query.
This helps understand what the user is trying to achieve with their question.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class IntentType(str, Enum):
    """Types of query intents."""
    ANALYTICS = "analytics"  # Analytical queries (trends, statistics)
    OPERATIONAL = "operational"  # Operational queries (current state)
    REPORTING = "reporting"  # Report generation queries
    COMPARISON = "comparison"  # Comparing data points
    AGGREGATION = "aggregation"  # Aggregating data
    LOOKUP = "lookup"  # Simple data lookup
    COUNT = "count"  # Counting entities
    SEARCH = "search"  # Searching for specific data
    PREDICTION = "prediction"  # Predictive queries
    UNKNOWN = "unknown"  # Unknown intent


class EntityType(str, Enum):
    """Types of entities mentioned in queries."""
    PRODUCT = "product"
    PHARMACY = "pharmacy"
    USER = "user"
    BOOKING = "booking"
    PAYMENT = "payment"
    PARTNER = "partner"
    SALE = "sale"
    RISK_GROUP = "risk_group"
    STOCK = "stock"
    CATEGORY = "category"


@dataclass(frozen=True)
class QueryIntent:
    """
    Immutable value object representing the intent of a query.

    This object captures what the user wants to do and what entities
    they're interested in, helping to route and optimize query execution.
    """

    # Core intent information
    type: IntentType  # The primary intent type
    confidence: float  # Confidence score (0.0 to 1.0)
    description: str  # Human-readable description of the intent

    # Entities involved
    entities: List[EntityType] = field(default_factory=list)  # Entity types mentioned
    entity_names: List[str] = field(default_factory=list)  # Specific entity names

    # Modifiers and constraints
    aggregations: List[str] = field(default_factory=list)  # sum, avg, count, etc.
    filters: Dict[str, Any] = field(default_factory=dict)  # Filter conditions
    sort_by: Optional[str] = None  # Sorting field
    limit: Optional[int] = None  # Result limit

    # Additional metadata
    requires_join: bool = False  # Whether multiple tables/collections needed
    complexity: str = "simple"  # simple, moderate, complex
    sub_intents: List[IntentType] = field(default_factory=list)  # Secondary intents

    def __post_init__(self):
        """
        Validate the query intent upon creation.

        Raises:
            ValueError: If validation fails
        """
        # Validate confidence score
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

        # Validate complexity
        valid_complexities = ["simple", "moderate", "complex"]
        if self.complexity not in valid_complexities:
            raise ValueError(f"Complexity must be one of {valid_complexities}, got {self.complexity}")

        # Auto-determine complexity if not properly set
        complexity_score = len(self.entities) + len(self.aggregations) + len(self.filters)
        if complexity_score <= 2:
            object.__setattr__(self, 'complexity', 'simple')
        elif complexity_score <= 5:
            object.__setattr__(self, 'complexity', 'moderate')
        else:
            object.__setattr__(self, 'complexity', 'complex')

    @classmethod
    def from_keywords(cls, text: str, keywords: List[str]) -> 'QueryIntent':
        """
        Create a QueryIntent from text analysis and keywords.

        Args:
            text: The original query text
            keywords: Extracted keywords from the query

        Returns:
            QueryIntent object
        """
        text_lower = text.lower()

        # Determine intent type
        intent_type = IntentType.UNKNOWN
        confidence = 0.5

        # Analytics keywords
        if any(word in text_lower for word in ['tendencia', 'trend', 'análisis', 'estadística']):
            intent_type = IntentType.ANALYTICS
            confidence = 0.8

        # Count keywords
        elif any(word in text_lower for word in ['cuántos', 'cuántas', 'cantidad', 'total']):
            intent_type = IntentType.COUNT
            confidence = 0.9

        # Comparison keywords
        elif any(word in text_lower for word in ['comparar', 'versus', 'diferencia', 'mayor', 'menor']):
            intent_type = IntentType.COMPARISON
            confidence = 0.85

        # Aggregation keywords
        elif any(word in text_lower for word in ['suma', 'promedio', 'máximo', 'mínimo', 'agrupar']):
            intent_type = IntentType.AGGREGATION
            confidence = 0.85

        # Search keywords
        elif any(word in text_lower for word in ['buscar', 'encontrar', 'listar', 'mostrar']):
            intent_type = IntentType.SEARCH
            confidence = 0.75

        # Reporting keywords
        elif any(word in text_lower for word in ['reporte', 'informe', 'resumen']):
            intent_type = IntentType.REPORTING
            confidence = 0.8

        # Operational keywords (default for current state queries)
        elif any(word in text_lower for word in ['activo', 'actual', 'ahora', 'disponible']):
            intent_type = IntentType.OPERATIONAL
            confidence = 0.7

        # Extract entities
        entities = []
        entity_names = []

        if 'producto' in text_lower or 'product' in text_lower:
            entities.append(EntityType.PRODUCT)
        if 'farmacia' in text_lower or 'pharmacy' in text_lower:
            entities.append(EntityType.PHARMACY)
        if 'usuario' in text_lower or 'user' in text_lower:
            entities.append(EntityType.USER)
        if 'booking' in text_lower or 'reserva' in text_lower:
            entities.append(EntityType.BOOKING)
        if 'pago' in text_lower or 'payment' in text_lower:
            entities.append(EntityType.PAYMENT)
        if any(partner in text_lower for partner in ['glovo', 'uber', 'danone', 'hartmann']):
            entities.append(EntityType.PARTNER)
            # Extract specific partner names
            for partner in ['glovo', 'uber', 'danone', 'hartmann', 'carrefour']:
                if partner in text_lower:
                    entity_names.append(partner.capitalize())

        # Extract aggregations
        aggregations = []
        if 'suma' in text_lower or 'total' in text_lower:
            aggregations.append('sum')
        if 'promedio' in text_lower or 'media' in text_lower:
            aggregations.append('avg')
        if 'máximo' in text_lower or 'max' in text_lower:
            aggregations.append('max')
        if 'mínimo' in text_lower or 'min' in text_lower:
            aggregations.append('min')
        if 'contar' in text_lower or 'count' in text_lower:
            aggregations.append('count')

        # Determine if join is required
        requires_join = len(entities) > 1

        return cls(
            type=intent_type,
            confidence=confidence,
            description=f"Query intent: {intent_type.value}",
            entities=entities,
            entity_names=entity_names,
            aggregations=aggregations,
            requires_join=requires_join
        )

    @property
    def is_high_confidence(self) -> bool:
        """
        Check if this is a high confidence intent.

        Returns:
            True if confidence >= 0.8
        """
        return self.confidence >= 0.8

    @property
    def is_analytical(self) -> bool:
        """
        Check if this is an analytical query.

        Returns:
            True if intent is analytical in nature
        """
        return self.type in [
            IntentType.ANALYTICS,
            IntentType.REPORTING,
            IntentType.COMPARISON,
            IntentType.PREDICTION
        ]

    @property
    def is_operational(self) -> bool:
        """
        Check if this is an operational query.

        Returns:
            True if intent is operational in nature
        """
        return self.type in [
            IntentType.OPERATIONAL,
            IntentType.LOOKUP,
            IntentType.COUNT,
            IntentType.SEARCH
        ]

    @property
    def needs_aggregation(self) -> bool:
        """
        Check if this query needs aggregation.

        Returns:
            True if aggregations are needed
        """
        return len(self.aggregations) > 0 or self.type == IntentType.AGGREGATION

    def get_recommended_database(self) -> str:
        """
        Get recommended database based on intent.

        Returns:
            Recommended database type
        """
        if self.is_analytical:
            return "mysql"  # Analytics go to MySQL
        elif EntityType.PHARMACY in self.entities or EntityType.BOOKING in self.entities:
            return "mongodb"  # Operational data in MongoDB
        elif EntityType.PRODUCT in self.entities and self.type == IntentType.ANALYTICS:
            return "mysql"  # Product analytics in MySQL
        else:
            return "mongodb"  # Default to MongoDB for operational

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'type': self.type.value,
            'confidence': self.confidence,
            'confidence_level': 'high' if self.is_high_confidence else 'medium',
            'description': self.description,
            'entities': [e.value for e in self.entities],
            'entity_names': self.entity_names,
            'aggregations': self.aggregations,
            'filters': self.filters,
            'sort_by': self.sort_by,
            'limit': self.limit,
            'requires_join': self.requires_join,
            'complexity': self.complexity,
            'sub_intents': [i.value for i in self.sub_intents],
            'is_analytical': self.is_analytical,
            'is_operational': self.is_operational,
            'needs_aggregation': self.needs_aggregation,
            'recommended_database': self.get_recommended_database()
        }

    def __str__(self) -> str:
        """String representation."""
        entities_str = f" on {', '.join(e.value for e in self.entities)}" if self.entities else ""
        return f"{self.type.value}{entities_str} (confidence: {self.confidence:.1%})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"QueryIntent(type={self.type.value}, "
            f"confidence={self.confidence:.2f}, "
            f"complexity={self.complexity})"
        )