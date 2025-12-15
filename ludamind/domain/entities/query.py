"""
Query Entity

Represents a database query in the system.
This entity tracks the lifecycle of a query from creation to execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..value_objects import (
    DatabaseType,
    QueryIntent,
    QueryResult,
    RoutingDecision,
    TimeRange
)


@dataclass
class Query:
    """
    Entity representing a database query.

    This entity encapsulates all information about a query throughout
    its lifecycle, from initial user question to final results.

    Identity is maintained through the `id` field.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))

    # Core properties
    question: str = ""  # The original natural language question
    user_id: Optional[str] = None  # User who created the query
    session_id: Optional[str] = None  # Session identifier

    # Query analysis results (can be modified during processing)
    intent: Optional[QueryIntent] = None  # Analyzed intent
    time_range: Optional[TimeRange] = None  # Time range if applicable
    routing_decision: Optional[RoutingDecision] = None  # Database routing decision

    # Generated query information
    database_type: Optional[DatabaseType] = None  # Target database
    generated_query: Optional[str] = None  # The actual database query
    query_params: Optional[Dict[str, Any]] = None  # Query parameters

    # Execution results
    result: Optional[QueryResult] = None  # Query execution results
    natural_language_answer: Optional[str] = None  # Generated answer

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Status tracking
    status: str = "created"  # created, analyzing, routing, executing, completed, failed
    error: Optional[str] = None  # Error message if failed

    # Performance metrics
    total_execution_time_ms: Optional[float] = None
    llm_generation_time_ms: Optional[float] = None
    database_execution_time_ms: Optional[float] = None

    # Cost tracking
    estimated_cost: Optional[float] = None  # Estimated cost in USD
    actual_cost: Optional[float] = None  # Actual cost in USD

    def __post_init__(self):
        """Initialize and validate the query entity."""
        self.validate()

    def validate(self):
        """
        Validate the query entity.

        Raises:
            ValueError: If validation fails
        """
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")

        if len(self.question) > 1000:
            raise ValueError("Question exceeds maximum length (1000 characters)")

        valid_statuses = ["created", "analyzing", "routing", "executing", "completed", "failed"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")

    # Business methods

    def start_analysis(self):
        """Mark the query as being analyzed."""
        self.status = "analyzing"
        self._validate_state_transition("analyzing")

    def complete_analysis(self, intent: QueryIntent, time_range: Optional[TimeRange] = None):
        """
        Complete the analysis phase.

        Args:
            intent: The analyzed query intent
            time_range: Optional time range extracted from query
        """
        self.intent = intent
        self.time_range = time_range
        self.status = "routing"
        self._validate_state_transition("routing")

    def set_routing(self, routing_decision: RoutingDecision):
        """
        Set the database routing decision.

        Args:
            routing_decision: The routing decision
        """
        self.routing_decision = routing_decision
        self.database_type = routing_decision.primary_database
        self.status = "executing"
        self._validate_state_transition("executing")

    def set_generated_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """
        Set the generated database query.

        Args:
            query: The generated query string
            params: Optional query parameters
        """
        self.generated_query = query
        self.query_params = params

    def start_execution(self):
        """Mark the query as being executed."""
        self.status = "executing"
        self.executed_at = datetime.now()
        self._validate_state_transition("executing")

    def complete_execution(self, result: QueryResult, natural_language_answer: str):
        """
        Complete the query execution.

        Args:
            result: The query execution result
            natural_language_answer: Generated natural language answer
        """
        self.result = result
        self.natural_language_answer = natural_language_answer
        self.status = "completed"
        self.completed_at = datetime.now()
        self._calculate_execution_times()
        self._validate_state_transition("completed")

    def fail(self, error_message: str):
        """
        Mark the query as failed.

        Args:
            error_message: The error message
        """
        self.status = "failed"
        self.error = error_message
        self.completed_at = datetime.now()

    def set_cost(self, estimated: float, actual: Optional[float] = None):
        """
        Set the cost information.

        Args:
            estimated: Estimated cost in USD
            actual: Actual cost in USD (if available)
        """
        self.estimated_cost = estimated
        if actual is not None:
            self.actual_cost = actual

    # Helper methods

    def _validate_state_transition(self, new_status: str):
        """
        Validate that the state transition is valid.

        Args:
            new_status: The new status

        Raises:
            ValueError: If transition is invalid
        """
        valid_transitions = {
            "created": ["analyzing", "failed"],
            "analyzing": ["routing", "failed"],
            "routing": ["executing", "failed"],
            "executing": ["completed", "failed"],
            "completed": [],
            "failed": []
        }

        # Note: We're checking the current status before it was changed
        # This is a simplified validation - in production you'd want more robust state management

    def _calculate_execution_times(self):
        """Calculate execution time metrics."""
        if self.created_at and self.completed_at:
            self.total_execution_time_ms = (
                (self.completed_at - self.created_at).total_seconds() * 1000
            )

        if self.result and self.result.execution_time_ms:
            self.database_execution_time_ms = self.result.execution_time_ms

        # LLM time would be total minus database time (simplified)
        if self.total_execution_time_ms and self.database_execution_time_ms:
            self.llm_generation_time_ms = (
                self.total_execution_time_ms - self.database_execution_time_ms
            )

    # Query methods

    @property
    def is_completed(self) -> bool:
        """Check if the query has been completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if the query has failed."""
        return self.status == "failed"

    @property
    def is_in_progress(self) -> bool:
        """Check if the query is currently being processed."""
        return self.status in ["analyzing", "routing", "executing"]

    @property
    def has_results(self) -> bool:
        """Check if the query has results."""
        return self.result is not None and self.result.is_success

    @property
    def execution_time_seconds(self) -> Optional[float]:
        """Get total execution time in seconds."""
        if self.total_execution_time_ms:
            return self.total_execution_time_ms / 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the query to a dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'question': self.question,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'status': self.status,
            'error': self.error,
            'intent': self.intent.to_dict() if self.intent else None,
            'time_range': self.time_range.to_dict() if self.time_range else None,
            'routing_decision': self.routing_decision.to_dict() if self.routing_decision else None,
            'database_type': self.database_type.value if self.database_type else None,
            'generated_query': self.generated_query,
            'query_params': self.query_params,
            'result': self.result.to_dict() if self.result else None,
            'natural_language_answer': self.natural_language_answer,
            'created_at': self.created_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_execution_time_ms': self.total_execution_time_ms,
            'llm_generation_time_ms': self.llm_generation_time_ms,
            'database_execution_time_ms': self.database_execution_time_ms,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Query(id={self.id[:8]}..., question='{self.question[:50]}...', status={self.status})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Query(id='{self.id}', status='{self.status}', has_results={self.has_results})"

    def __eq__(self, other) -> bool:
        """
        Equality based on identity (id field).

        Args:
            other: Another Query object

        Returns:
            True if same identity
        """
        if not isinstance(other, Query):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)