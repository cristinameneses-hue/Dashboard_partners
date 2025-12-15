"""
Execute Query Use Case

Core business logic for executing database queries.
This use case orchestrates the entire query execution flow.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from domain.entities import Query, User, Conversation
from domain.repositories import DatabaseRepository, LLMRepository
from domain.value_objects import (
    DatabaseType,
    QueryResult,
    QueryIntent,
    TimeRange,
    RoutingDecision
)


logger = logging.getLogger(__name__)


class ExecuteQueryUseCase:
    """
    Use case for executing natural language queries.

    This class encapsulates the business logic for:
    1. Analyzing query intent
    2. Routing to appropriate database
    3. Generating database query
    4. Executing query
    5. Generating natural language answer

    Follows Single Responsibility Principle - only handles query execution flow.
    """

    def __init__(self,
                 mysql_repository: Optional[DatabaseRepository] = None,
                 mongodb_repository: Optional[DatabaseRepository] = None,
                 llm_repository: Optional[LLMRepository] = None):
        """
        Initialize the use case.

        Args:
            mysql_repository: Repository for MySQL operations
            mongodb_repository: Repository for MongoDB operations
            llm_repository: Repository for LLM operations
        """
        self.mysql_repository = mysql_repository
        self.mongodb_repository = mongodb_repository
        self.llm_repository = llm_repository

        # Metrics
        self.total_queries_executed = 0
        self.total_execution_time_ms = 0.0
        self.success_count = 0
        self.failure_count = 0

    async def execute(self,
                     question: str,
                     user: Optional[User] = None,
                     conversation: Optional[Conversation] = None,
                     context: Optional[Dict[str, Any]] = None) -> Query:
        """
        Execute a natural language query.

        Args:
            question: Natural language question
            user: User executing the query (for permissions/quotas)
            conversation: Current conversation (for context)
            context: Additional context

        Returns:
            Query entity with results

        Raises:
            ValueError: If validation fails
            RuntimeError: If execution fails
        """
        start_time = time.time()

        # Create query entity
        query = Query(
            question=question,
            user_id=user.id if user else None,
            session_id=conversation.id if conversation else None
        )

        try:
            # Step 1: Validate user permissions
            if user:
                self._validate_user_permissions(user, query)

            # Step 2: Analyze query intent
            query = await self._analyze_intent(query, context)

            # Step 3: Route query to appropriate database
            query = await self._route_query(query, context)

            # Step 4: Generate database query
            query = await self._generate_query(query, context)

            # Step 5: Execute database query
            query = await self._execute_database_query(query)

            # Step 6: Generate natural language answer
            query = await self._generate_answer(query, context)

            # Step 7: Update metrics and complete
            query.complete_execution(
                result=query.result,
                natural_language_answer=query.natural_language_answer
            )

            # Update user metrics if applicable
            if user:
                await self._update_user_metrics(user, query)

            # Add to conversation if applicable
            if conversation:
                conversation.add_query(query.id)
                conversation.add_message(
                    role="user",
                    content=question,
                    token_count=len(question.split()) * 2  # Rough estimate
                )
                conversation.add_message(
                    role="assistant",
                    content=query.natural_language_answer,
                    token_count=len(query.natural_language_answer.split()) * 2,
                    cost_usd=query.actual_cost
                )

            # Update use case metrics
            self.total_queries_executed += 1
            self.total_execution_time_ms += (time.time() - start_time) * 1000
            self.success_count += 1

            logger.info(
                f"Query executed successfully: {query.id[:8]} "
                f"({query.database_type.value}, "
                f"{query.total_execution_time_ms:.0f}ms)"
            )

            return query

        except Exception as e:
            # Mark query as failed
            query.fail(str(e))
            self.failure_count += 1

            logger.error(f"Query execution failed: {str(e)}")
            raise

    def _validate_user_permissions(self, user: User, query: Query):
        """
        Validate user permissions and quotas.

        Args:
            user: User to validate
            query: Query being executed

        Raises:
            ValueError: If validation fails
        """
        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is not active")

        # Check if user is locked
        if user.is_locked:
            raise ValueError(f"User account is locked: {user.lock_reason}")

        # Check query permission
        if not user.can_query:
            raise ValueError("User does not have permission to execute queries")

        # Check quota
        if user.quota_exceeded:
            raise ValueError("User quota exceeded. Please upgrade your subscription.")

        # Check database access (will be checked after routing)
        # This is a placeholder for now

    async def _analyze_intent(self,
                             query: Query,
                             context: Optional[Dict[str, Any]]) -> Query:
        """
        Analyze query intent using LLM.

        Args:
            query: Query entity
            context: Additional context

        Returns:
            Updated query with intent
        """
        query.start_analysis()

        if not self.llm_repository:
            # Fallback to basic keyword analysis
            intent = QueryIntent.from_keywords(query.question, query.question.split())
            query.complete_analysis(intent)
            return query

        try:
            # Use LLM for advanced intent analysis
            intent_data = await self.llm_repository.analyze_intent(
                query.question,
                context
            )

            # Create QueryIntent from LLM response
            intent = QueryIntent(
                type=intent_data.get('type', 'unknown'),
                confidence=float(intent_data.get('confidence', 0.5)),
                description=intent_data.get('description', ''),
                entities=intent_data.get('entities', []),
                aggregations=intent_data.get('aggregations', []),
                requires_join=intent_data.get('requires_join', False)
            )

            # Extract time range if present
            time_range = None
            if intent_data.get('time_range'):
                time_range = TimeRange.from_spanish_expression(
                    intent_data['time_range']
                )

            query.complete_analysis(intent, time_range)

        except Exception as e:
            logger.warning(f"LLM intent analysis failed, using fallback: {e}")
            # Fallback to keyword analysis
            intent = QueryIntent.from_keywords(query.question, query.question.split())
            query.complete_analysis(intent)

        return query

    async def _route_query(self,
                          query: Query,
                          context: Optional[Dict[str, Any]]) -> Query:
        """
        Route query to appropriate database.

        Args:
            query: Query entity
            context: Additional context

        Returns:
            Updated query with routing decision
        """
        # Use intent to determine routing
        if query.intent:
            recommended_db = query.intent.get_recommended_database()
            database_type = (
                DatabaseType.MYSQL if recommended_db == "mysql"
                else DatabaseType.MONGODB
            )
        else:
            # Fallback to keyword-based routing
            database_type = self._keyword_based_routing(query.question)

        # Create routing decision
        routing_decision = RoutingDecision(
            primary_database=database_type,
            confidence=query.intent.confidence if query.intent else 0.5,
            reasoning=f"Based on {'intent analysis' if query.intent else 'keyword matching'}"
        )

        # Check for cross-database requirements
        if query.intent and query.intent.requires_join:
            routing_decision.requires_cross_database = True
            routing_decision.secondary_databases = [
                DatabaseType.MONGODB if database_type == DatabaseType.MYSQL
                else DatabaseType.MYSQL
            ]

        query.set_routing(routing_decision)
        return query

    async def _generate_query(self,
                             query: Query,
                             context: Optional[Dict[str, Any]]) -> Query:
        """
        Generate database query using LLM.

        Args:
            query: Query entity
            context: Additional context

        Returns:
            Updated query with generated database query
        """
        if not self.llm_repository:
            raise RuntimeError("LLM repository is required for query generation")

        # Get appropriate repository
        repository = (
            self.mysql_repository if query.database_type == DatabaseType.MYSQL
            else self.mongodb_repository
        )

        if not repository:
            raise RuntimeError(f"No repository available for {query.database_type.value}")

        # Prepare context with schema information
        enhanced_context = context or {}

        if query.database_type == DatabaseType.MYSQL:
            # Add table schema for MySQL
            if hasattr(repository, 'list_tables'):
                tables = await repository.list_tables()
                enhanced_context['schema'] = {'tables': tables}
        else:
            # Add collection info for MongoDB
            if hasattr(repository, 'list_collections'):
                collections = await repository.list_collections()
                enhanced_context['collections'] = collections

        # Generate query using LLM
        query_spec = await self.llm_repository.generate_query(
            question=query.question,
            database_type=query.database_type,
            context=enhanced_context
        )

        # Validate generated query
        is_valid, error_msg = await self.llm_repository.validate_query(
            query_spec.query,
            query.database_type
        )

        if not is_valid:
            raise ValueError(f"Generated query validation failed: {error_msg}")

        # Set generated query
        query.set_generated_query(
            query_spec.query,
            query_spec.parameters
        )

        # Store generation metadata
        if query_spec.metadata:
            query.llm_generation_time_ms = query_spec.metadata.get('generation_time_ms', 0)
            query.estimated_cost = query_spec.metadata.get('cost_usd', 0)

        return query

    async def _execute_database_query(self, query: Query) -> Query:
        """
        Execute the generated database query.

        Args:
            query: Query entity

        Returns:
            Updated query with results
        """
        query.start_execution()

        # Get appropriate repository
        repository = (
            self.mysql_repository if query.database_type == DatabaseType.MYSQL
            else self.mongodb_repository
        )

        if not repository:
            raise RuntimeError(f"No repository available for {query.database_type.value}")

        try:
            start_time = time.time()

            # Execute query
            if query.database_type == DatabaseType.MYSQL:
                # Execute SQL query
                results = await repository.execute_query(
                    query.generated_query,
                    query.query_params
                )
            else:
                # Execute MongoDB query (query is JSON)
                results = await repository.execute_query(
                    query.generated_query,
                    query.query_params
                )

            execution_time_ms = (time.time() - start_time) * 1000

            # Create QueryResult
            query_result = QueryResult(
                data=results,
                count=len(results),
                is_success=True,
                execution_time_ms=execution_time_ms,
                database_type=query.database_type,
                query_executed=query.generated_query
            )

            query.result = query_result
            query.database_execution_time_ms = execution_time_ms

        except Exception as e:
            # Create error result
            query.result = QueryResult(
                data=[],
                count=0,
                is_success=False,
                error_message=str(e),
                database_type=query.database_type,
                query_executed=query.generated_query
            )
            raise RuntimeError(f"Database query execution failed: {e}")

        return query

    async def _generate_answer(self,
                              query: Query,
                              context: Optional[Dict[str, Any]]) -> Query:
        """
        Generate natural language answer from results.

        Args:
            query: Query entity
            context: Additional context

        Returns:
            Updated query with answer
        """
        if not self.llm_repository:
            # Fallback to simple answer
            if query.result and query.result.is_success:
                query.natural_language_answer = (
                    f"Found {query.result.count} results. "
                    f"Query executed in {query.result.execution_time_ms:.0f}ms."
                )
            else:
                query.natural_language_answer = "Query execution failed."
            return query

        try:
            # Generate answer using LLM
            answer = await self.llm_repository.generate_answer(
                question=query.question,
                results=query.result.data if query.result else [],
                context=context
            )

            query.natural_language_answer = answer

        except Exception as e:
            logger.warning(f"Answer generation failed, using fallback: {e}")
            # Fallback answer
            if query.result and query.result.is_success:
                query.natural_language_answer = (
                    f"Query completed successfully with {query.result.count} results."
                )
            else:
                query.natural_language_answer = "Unable to generate answer."

        return query

    async def _update_user_metrics(self, user: User, query: Query):
        """
        Update user metrics after query execution.

        Args:
            user: User who executed query
            query: Completed query
        """
        # Calculate token usage (approximate)
        tokens_used = (
            len(query.question.split()) * 2 +  # Input tokens
            len(query.natural_language_answer.split()) * 2  # Output tokens
        )

        # Update user metrics
        user.record_query(
            tokens_used=tokens_used,
            cost_usd=query.actual_cost or query.estimated_cost or 0.0
        )

    def _keyword_based_routing(self, question: str) -> DatabaseType:
        """
        Simple keyword-based database routing.

        Args:
            question: Question text

        Returns:
            Database type
        """
        question_lower = question.lower()

        mysql_keywords = [
            'ventas', 'sales', 'trends', 'tendencia',
            'z_y', 'riesgo', 'predicción', 'análisis'
        ]

        mongodb_keywords = [
            'farmacia', 'usuario', 'booking', 'catálogo',
            'stock', 'partner', 'gmv', 'glovo', 'uber'
        ]

        mysql_score = sum(1 for kw in mysql_keywords if kw in question_lower)
        mongodb_score = sum(1 for kw in mongodb_keywords if kw in question_lower)

        return DatabaseType.MYSQL if mysql_score > mongodb_score else DatabaseType.MONGODB

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get use case execution metrics.

        Returns:
            Metrics dictionary
        """
        return {
            'total_queries': self.total_queries_executed,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': (
                self.success_count / self.total_queries_executed
                if self.total_queries_executed > 0 else 0.0
            ),
            'average_execution_time_ms': (
                self.total_execution_time_ms / self.total_queries_executed
                if self.total_queries_executed > 0 else 0.0
            )
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecuteQueryUseCase("
            f"queries={self.total_queries_executed}, "
            f"success_rate={self.success_count/max(self.total_queries_executed, 1):.1%}"
            f")"
        )