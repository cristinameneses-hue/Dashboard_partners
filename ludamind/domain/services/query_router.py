"""
Query Router Service

Domain service responsible for determining which database should handle a query
based on its content and context. This service encapsulates the routing logic
and rules for database selection.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import re
from enum import Enum

from ..value_objects.database_type import DatabaseType
from ..value_objects.routing_decision import RoutingDecision
from ..entities.query import Query


class RoutingStrategy(Enum):
    """Available routing strategies."""
    KEYWORD_BASED = "keyword_based"
    ML_BASED = "ml_based"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"


@dataclass
class QueryRouterService:
    """
    Service for routing queries to appropriate databases.

    This domain service analyzes queries and determines which database
    (MySQL or MongoDB) should handle them based on keywords, patterns,
    and business rules.

    Attributes:
        routing_strategy: Strategy to use for routing
        mysql_keywords: Keywords that indicate MySQL database
        mongodb_keywords: Keywords that indicate MongoDB database
        default_database: Default database when routing is uncertain
        confidence_threshold: Minimum confidence for routing decision
    """

    routing_strategy: RoutingStrategy = RoutingStrategy.KEYWORD_BASED
    default_database: DatabaseType = DatabaseType.MONGODB
    confidence_threshold: float = 0.6

    # MySQL keywords - Analytics and trends
    mysql_keywords: Set[str] = None

    # MongoDB keywords - Operations and real-time
    mongodb_keywords: Set[str] = None

    def __post_init__(self):
        """Initialize keyword sets if not provided."""
        if self.mysql_keywords is None:
            self.mysql_keywords = {
                # Sales and analytics
                "ventas", "vendidos", "sold", "sales", "revenue", "gmv",
                "trends", "tendencias", "demanda", "demand", "análisis",

                # Risk and scoring
                "z_y", "z-score", "riesgo", "risk", "grupo de riesgo",
                "risk group", "scoring", "predicción", "prediction",

                # Cazador/Hunter
                "cazador", "hunter", "opportunities", "oportunidades",

                # Performance and metrics
                "performance", "metrics", "kpi", "estadísticas", "statistics",
                "histórico", "historical", "consolidado", "aggregated",

                # Time-based analytics
                "último mes", "last month", "últimos días", "last days",
                "esta semana", "this week", "año pasado", "last year",

                # Products analytics
                "productos más", "top products", "más vendidos", "best selling",
                "menos vendidos", "worst selling", "rotación", "rotation"
            }

        if self.mongodb_keywords is None:
            self.mongodb_keywords = {
                # Pharmacy operations
                "farmacia", "pharmacy", "farmacias", "pharmacies",
                "sucursal", "branch", "tienda", "store", "activas", "active",

                # User management
                "usuario", "user", "usuarios", "users", "cliente", "client",
                "cuenta", "account", "registro", "registration",

                # Bookings and reservations
                "booking", "reserva", "derivación", "derivaciones",
                "pedido", "pedidos", "order", "orders", "pending",

                # Catalog and inventory
                "catálogo", "catalog", "producto", "product", "item",
                "stock actual", "current stock", "inventario", "inventory",
                "disponible", "available", "agotado", "out of stock",

                # Payments and billing
                "pago", "payment", "factura", "invoice", "billing",
                "cobro", "charge", "transacción", "transaction",

                # Partners
                "partner", "proveedor", "provider", "glovo", "uber",
                "danone", "hartmann", "carrefour", "rappi", "didi",

                # Notifications
                "notificación", "notification", "alerta", "alert",
                "mensaje", "message", "push", "email",

                # Real-time operations
                "ahora", "now", "actual", "current", "real-time",
                "en este momento", "at this moment", "hoy", "today"
            }

    def route_query(self, query: Query) -> RoutingDecision:
        """
        Route a query to the appropriate database.

        Args:
            query: Query entity to route

        Returns:
            RoutingDecision with database selection and confidence
        """
        if self.routing_strategy == RoutingStrategy.KEYWORD_BASED:
            return self._keyword_based_routing(query)
        elif self.routing_strategy == RoutingStrategy.RULE_BASED:
            return self._rule_based_routing(query)
        elif self.routing_strategy == RoutingStrategy.HYBRID:
            return self._hybrid_routing(query)
        else:
            # ML-based routing would require a trained model
            return self._keyword_based_routing(query)

    def _keyword_based_routing(self, query: Query) -> RoutingDecision:
        """
        Route based on keyword matching.

        Args:
            query: Query to analyze

        Returns:
            RoutingDecision based on keyword analysis
        """
        query_text = query.text.lower()

        # Count keyword matches
        mysql_score = self._calculate_keyword_score(query_text, self.mysql_keywords)
        mongodb_score = self._calculate_keyword_score(query_text, self.mongodb_keywords)

        # Calculate confidence
        total_score = mysql_score + mongodb_score
        if total_score == 0:
            # No keywords found, use default
            return RoutingDecision(
                primary_database=self.default_database,
                confidence=0.3,
                keyword_scores={DatabaseType.MYSQL: 0, DatabaseType.MONGODB: 0},
                matched_keywords={DatabaseType.MYSQL: [], DatabaseType.MONGODB: []},
                reasoning="No specific keywords found, using default database"
            )

        # Determine winner
        if mysql_score > mongodb_score:
            confidence = mysql_score / total_score
            mysql_matched = self._get_matched_keywords(query_text, self.mysql_keywords)
            mongodb_matched = self._get_matched_keywords(query_text, self.mongodb_keywords)

            return RoutingDecision(
                primary_database=DatabaseType.MYSQL,
                confidence=confidence,
                keyword_scores={DatabaseType.MYSQL: int(mysql_score), DatabaseType.MONGODB: int(mongodb_score)},
                matched_keywords={DatabaseType.MYSQL: mysql_matched, DatabaseType.MONGODB: mongodb_matched},
                reasoning=f"Query contains MySQL indicators: {', '.join(mysql_matched)}",
                alternative_database=DatabaseType.MONGODB if mongodb_score > 0 else None,
                alternative_confidence=mongodb_score / total_score if mongodb_score > 0 else None
            )
        else:
            confidence = mongodb_score / total_score
            mysql_matched = self._get_matched_keywords(query_text, self.mysql_keywords)
            mongodb_matched = self._get_matched_keywords(query_text, self.mongodb_keywords)

            return RoutingDecision(
                primary_database=DatabaseType.MONGODB,
                confidence=confidence,
                keyword_scores={DatabaseType.MYSQL: int(mysql_score), DatabaseType.MONGODB: int(mongodb_score)},
                matched_keywords={DatabaseType.MYSQL: mysql_matched, DatabaseType.MONGODB: mongodb_matched},
                reasoning=f"Query contains MongoDB indicators: {', '.join(mongodb_matched)}",
                alternative_database=DatabaseType.MYSQL if mysql_score > 0 else None,
                alternative_confidence=mysql_score / total_score if mysql_score > 0 else None
            )

    def _rule_based_routing(self, query: Query) -> RoutingDecision:
        """
        Route based on predefined rules.

        Args:
            query: Query to analyze

        Returns:
            RoutingDecision based on rules
        """
        query_text = query.text.lower()

        # Rule 1: Partner GMV queries always go to MongoDB
        if "gmv" in query_text and any(partner in query_text for partner in
                                       ["glovo", "uber", "danone", "hartmann", "carrefour"]):
            return RoutingDecision(
                primary_database=DatabaseType.MONGODB,
                confidence=0.95,
                keyword_scores={DatabaseType.MYSQL: 0, DatabaseType.MONGODB: 2},
                matched_keywords={DatabaseType.MYSQL: [], DatabaseType.MONGODB: ["gmv", "partner"]},
                reasoning="Partner GMV queries use MongoDB bookings collection"
            )

        # Rule 2: Risk group queries always go to MySQL
        if "grupo de riesgo" in query_text or "risk group" in query_text:
            return RoutingDecision(
                primary_database=DatabaseType.MYSQL,
                confidence=0.95,
                keyword_scores={DatabaseType.MYSQL: 1, DatabaseType.MONGODB: 0},
                matched_keywords={DatabaseType.MYSQL: ["risk group"], DatabaseType.MONGODB: []},
                reasoning="Risk group analysis uses MySQL trends database"
            )

        # Rule 3: Z_Y score queries always go to MySQL
        if re.search(r'z[_\-]y|z score', query_text):
            return RoutingDecision(
                primary_database=DatabaseType.MYSQL,
                confidence=0.95,
                keyword_scores={DatabaseType.MYSQL: 1, DatabaseType.MONGODB: 0},
                matched_keywords={DatabaseType.MYSQL: ["z_y score"], DatabaseType.MONGODB: []},
                reasoning="Z_Y score analysis uses MySQL trends database"
            )

        # Rule 4: Active pharmacy counts go to MongoDB
        if re.search(r'cuántas?\s+farmacias?\s+(hay|tenemos|activas?)', query_text):
            return RoutingDecision(
                primary_database=DatabaseType.MONGODB,
                confidence=0.90,
                keyword_scores={DatabaseType.MYSQL: 0, DatabaseType.MONGODB: 2},
                matched_keywords={DatabaseType.MYSQL: [], DatabaseType.MONGODB: ["farmacias", "activas"]},
                reasoning="Pharmacy counts use MongoDB pharmacies collection"
            )

        # Rule 5: Product sales analysis goes to MySQL
        if re.search(r'productos?\s+más\s+vendidos?|top\s+\d+\s+productos?', query_text):
            return RoutingDecision(
                primary_database=DatabaseType.MYSQL,
                confidence=0.90,
                keyword_scores={DatabaseType.MYSQL: 2, DatabaseType.MONGODB: 0},
                matched_keywords={DatabaseType.MYSQL: ["productos", "vendidos"], DatabaseType.MONGODB: []},
                reasoning="Sales analysis uses MySQL analytics database"
            )

        # Fall back to keyword-based routing
        return self._keyword_based_routing(query)

    def _hybrid_routing(self, query: Query) -> RoutingDecision:
        """
        Combine multiple routing strategies.

        Args:
            query: Query to analyze

        Returns:
            RoutingDecision combining multiple strategies
        """
        # Get decisions from different strategies
        rule_decision = self._rule_based_routing(query)
        keyword_decision = self._keyword_based_routing(query)

        # If rule-based has high confidence, use it
        if rule_decision.confidence >= 0.90:
            return rule_decision

        # Otherwise, combine decisions
        if rule_decision.primary_database == keyword_decision.primary_database:
            # Agreement between strategies
            combined_confidence = min(1.0, (rule_decision.confidence + keyword_decision.confidence) / 2 * 1.2)

            # Combine matched keywords from both decisions
            combined_mysql_keywords = list(set(
                rule_decision.matched_keywords.get(DatabaseType.MYSQL, []) +
                keyword_decision.matched_keywords.get(DatabaseType.MYSQL, [])
            ))
            combined_mongodb_keywords = list(set(
                rule_decision.matched_keywords.get(DatabaseType.MONGODB, []) +
                keyword_decision.matched_keywords.get(DatabaseType.MONGODB, [])
            ))

            # Combine keyword scores
            combined_scores = {
                DatabaseType.MYSQL: rule_decision.keyword_scores.get(DatabaseType.MYSQL, 0) +
                                   keyword_decision.keyword_scores.get(DatabaseType.MYSQL, 0),
                DatabaseType.MONGODB: rule_decision.keyword_scores.get(DatabaseType.MONGODB, 0) +
                                     keyword_decision.keyword_scores.get(DatabaseType.MONGODB, 0)
            }

            return RoutingDecision(
                primary_database=rule_decision.primary_database,
                confidence=combined_confidence,
                keyword_scores=combined_scores,
                matched_keywords={
                    DatabaseType.MYSQL: combined_mysql_keywords,
                    DatabaseType.MONGODB: combined_mongodb_keywords
                },
                reasoning=f"Multiple strategies agree: {rule_decision.reasoning}"
            )
        else:
            # Disagreement - use the one with higher confidence
            if rule_decision.confidence > keyword_decision.confidence:
                return rule_decision
            else:
                return keyword_decision

    def _calculate_keyword_score(self, text: str, keywords: Set[str]) -> float:
        """
        Calculate keyword matching score.

        Args:
            text: Text to analyze
            keywords: Set of keywords to match

        Returns:
            Score based on keyword matches
        """
        score = 0.0
        words = set(text.lower().split())

        for keyword in keywords:
            if " " in keyword:
                # Multi-word keyword
                if keyword in text:
                    score += 2.0  # Higher weight for phrase matches
            elif keyword in words:
                score += 1.0

        return score

    def _get_matched_keywords(self, text: str, keywords: Set[str]) -> List[str]:
        """
        Get list of matched keywords.

        Args:
            text: Text to analyze
            keywords: Set of keywords to check

        Returns:
            List of keywords found in text
        """
        matched = []
        words = set(text.lower().split())

        for keyword in keywords:
            if " " in keyword:
                # Multi-word keyword
                if keyword in text:
                    matched.append(keyword)
            elif keyword in words:
                matched.append(keyword)

        return matched[:5]  # Return top 5 matches

    def analyze_query_complexity(self, query: Query) -> Dict[str, any]:
        """
        Analyze query complexity and characteristics.

        Args:
            query: Query to analyze

        Returns:
            Dictionary with complexity analysis
        """
        text = query.text.lower()

        # Check for cross-database indicators
        mysql_matches = self._get_matched_keywords(text, self.mysql_keywords)
        mongodb_matches = self._get_matched_keywords(text, self.mongodb_keywords)

        is_complex = len(mysql_matches) > 0 and len(mongodb_matches) > 0

        # Check for temporal indicators
        temporal_patterns = [
            r'últimos?\s+\d+\s+(días?|semanas?|meses?)',
            r'desde\s+\w+',
            r'entre\s+\w+\s+y\s+\w+',
            r'(ayer|hoy|mañana)',
            r'esta\s+(semana|mes|año)',
            r'(semana|mes|año)\s+pasad[oa]'
        ]
        has_temporal = any(re.search(pattern, text) for pattern in temporal_patterns)

        # Check for aggregation indicators
        aggregation_patterns = [
            r'total',
            r'suma',
            r'promedio|average',
            r'máximo|máxima|max',
            r'mínimo|mínima|min',
            r'contar|count',
            r'agrupar|group\s+by'
        ]
        requires_aggregation = any(re.search(pattern, text) for pattern in aggregation_patterns)

        return {
            "is_complex": is_complex,
            "requires_join": is_complex,
            "mysql_indicators": mysql_matches,
            "mongodb_indicators": mongodb_matches,
            "has_temporal_component": has_temporal,
            "requires_aggregation": requires_aggregation,
            "estimated_difficulty": "high" if is_complex else "medium" if requires_aggregation else "low",
            "suggested_databases": self._suggest_databases(mysql_matches, mongodb_matches)
        }

    def _suggest_databases(
        self,
        mysql_matches: List[str],
        mongodb_matches: List[str]
    ) -> List[DatabaseType]:
        """
        Suggest databases based on matched keywords.

        Args:
            mysql_matches: MySQL keyword matches
            mongodb_matches: MongoDB keyword matches

        Returns:
            List of suggested databases in priority order
        """
        if not mysql_matches and not mongodb_matches:
            return [self.default_database]

        if mysql_matches and not mongodb_matches:
            return [DatabaseType.MYSQL]

        if mongodb_matches and not mysql_matches:
            return [DatabaseType.MONGODB]

        # Both have matches - order by count
        if len(mysql_matches) > len(mongodb_matches):
            return [DatabaseType.MYSQL, DatabaseType.MONGODB]
        else:
            return [DatabaseType.MONGODB, DatabaseType.MYSQL]

    def get_routing_explanation(self, query: Query) -> str:
        """
        Get a human-readable explanation of routing decision.

        Args:
            query: Query that was routed

        Returns:
            Explanation string
        """
        decision = self.route_query(query)
        complexity = self.analyze_query_complexity(query)

        explanation = f"Query: '{query.text[:100]}...'\n\n"
        explanation += f"Routing Decision: {decision.primary_database.value.upper()}\n"
        explanation += f"Confidence: {decision.confidence:.2%}\n"
        explanation += f"Reasoning: {decision.reasoning}\n\n"

        # Collect all matched keywords from both databases
        all_keywords = []
        for db_type, keywords in decision.matched_keywords.items():
            all_keywords.extend(keywords)

        if all_keywords:
            explanation += f"Matched Keywords: {', '.join(all_keywords)}\n\n"

        explanation += "Complexity Analysis:\n"
        explanation += f"- Difficulty: {complexity['estimated_difficulty']}\n"
        explanation += f"- Cross-database query: {'Yes' if complexity['is_complex'] else 'No'}\n"
        explanation += f"- Temporal component: {'Yes' if complexity['has_temporal_component'] else 'No'}\n"
        explanation += f"- Requires aggregation: {'Yes' if complexity['requires_aggregation'] else 'No'}\n"

        return explanation

    def validate_routing_decision(
        self,
        decision: RoutingDecision,
        actual_database: DatabaseType
    ) -> bool:
        """
        Validate if a routing decision was correct.

        This method can be used for monitoring and improving routing accuracy.

        Args:
            decision: The routing decision that was made
            actual_database: The database that actually handled the query

        Returns:
            True if decision was correct, False otherwise
        """
        return decision.primary_database == actual_database

    def update_routing_rules(
        self,
        feedback: List[Tuple[Query, DatabaseType]]
    ) -> None:
        """
        Update routing rules based on feedback.

        This method allows the service to learn from correct routing decisions.

        Args:
            feedback: List of (query, correct_database) tuples
        """
        # This could be implemented to:
        # 1. Update keyword weights
        # 2. Add new keywords
        # 3. Adjust confidence thresholds
        # 4. Train ML models if using ML-based routing

        # For now, just log the feedback
        for query, correct_db in feedback:
            decision = self.route_query(query)
            if decision.primary_database != correct_db:
                # Log incorrect routing for analysis
                print(f"Incorrect routing: Query '{query.text[:50]}...' "
                      f"routed to {decision.primary_database.value} "
                      f"but should be {correct_db.value}")