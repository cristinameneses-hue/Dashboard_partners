"""
OpenAI LLM Repository Implementation

Concrete implementation of LLMRepository for OpenAI GPT models.
Follows SOLID principles with streaming support and cost tracking.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from datetime import datetime
import json
import time
from dataclasses import dataclass, field

import openai
from openai import AsyncOpenAI

from domain.repositories import LLMRepository
from domain.value_objects import DatabaseType, QuerySpec


logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for OpenAI models."""
    name: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60

    # Cost tracking (per 1K tokens)
    input_cost_per_1k: float = 0.0015  # GPT-4o-mini pricing
    output_cost_per_1k: float = 0.006

    # System prompts
    query_generation_prompt: str = field(default_factory=lambda: """
You are an expert database query generator. Your task is to convert natural language questions
into appropriate database queries (SQL for MySQL or MongoDB queries).

Rules:
1. Generate only SELECT queries for MySQL (no modifications)
2. Generate only find/aggregate queries for MongoDB (no modifications)
3. Be precise and efficient in your queries
4. Include appropriate JOINs when needed for MySQL
5. Use proper aggregation pipelines for MongoDB when needed
6. Always limit results appropriately (default 100)

Return the query in a structured format.
""")

    answer_generation_prompt: str = field(default_factory=lambda: """
You are a helpful assistant that explains database query results in natural language.
Your task is to convert raw database results into clear, concise answers in Spanish.

Rules:
1. Be concise and direct
2. Use proper formatting for numbers and dates
3. Highlight key insights from the data
4. If the data is empty, explain clearly that no results were found
5. Use bullet points or tables when appropriate
6. Always respond in Spanish
""")


class OpenAILLMRepository(LLMRepository):
    """
    OpenAI LLM repository implementation.

    Implements the LLMRepository interface for OpenAI GPT models,
    providing query generation, answer generation, and streaming support.
    """

    def __init__(self,
                 api_key: str,
                 organization: Optional[str] = None,
                 model_config: Optional[ModelConfig] = None):
        """
        Initialize OpenAI LLM repository.

        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            model_config: Model configuration
        """
        self.api_key = api_key
        self.organization = organization
        self.config = model_config or ModelConfig()

        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            timeout=self.config.timeout
        )

        # Metrics tracking
        self.total_requests = 0
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.last_request_tokens = 0
        self.last_request_cost = 0.0

    async def generate_query(self,
                            question: str,
                            database_type: DatabaseType,
                            context: Optional[Dict[str, Any]] = None) -> QuerySpec:
        """
        Generate a database query from natural language.

        Args:
            question: Natural language question
            database_type: Type of database (MySQL or MongoDB)
            context: Optional context (schema, examples, etc.)

        Returns:
            QuerySpec with generated query
        """
        start_time = time.time()

        # Build the prompt
        system_prompt = self._build_query_generation_prompt(database_type, context)

        try:
            # Create completion
            response = await self.client.chat.completions.create(
                model=self.config.name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            query_data = json.loads(content)

            # Track metrics
            self._track_usage(response.usage)

            execution_time = (time.time() - start_time) * 1000

            return QuerySpec(
                query=query_data.get('query', ''),
                database_type=database_type,
                parameters=query_data.get('parameters', {}),
                options=query_data.get('options', {}),
                metadata={
                    'model': self.config.name,
                    'tokens_used': response.usage.total_tokens,
                    'generation_time_ms': execution_time,
                    'cost_usd': self.last_request_cost
                }
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise ValueError(f"Invalid query generation response: {str(e)}")
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}")
            raise RuntimeError(f"Query generation failed: {str(e)}")

    async def generate_answer(self,
                             question: str,
                             results: List[Dict[str, Any]],
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a natural language answer from query results.

        Args:
            question: Original question
            results: Query results
            context: Optional context

        Returns:
            Natural language answer
        """
        start_time = time.time()

        # Build the prompt
        system_prompt = self._build_answer_generation_prompt(context)
        user_prompt = self._format_results_for_answer(question, results)

        try:
            # Create completion
            response = await self.client.chat.completions.create(
                model=self.config.name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p
            )

            # Track metrics
            self._track_usage(response.usage)

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            raise RuntimeError(f"Answer generation failed: {str(e)}")

    async def generate_stream(self,
                             messages: List[Dict[str, str]],
                             context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Generate streaming response.

        Args:
            messages: Conversation messages
            context: Optional context

        Yields:
            Response tokens as they arrive
        """
        try:
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=self.config.name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True
            )

            # Track tokens for cost calculation
            token_count = 0

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    token_count += len(content.split())  # Approximate
                    yield content

            # Approximate cost tracking for streaming
            self._track_streaming_usage(token_count, messages)

        except Exception as e:
            logger.error(f"Streaming generation failed: {str(e)}")
            raise RuntimeError(f"Streaming generation failed: {str(e)}")

    async def analyze_intent(self,
                            question: str,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the intent of a question.

        Args:
            question: Natural language question
            context: Optional context

        Returns:
            Intent analysis with confidence scores
        """
        prompt = f"""
Analyze the following question and determine:
1. The type of query (analytics, operational, reporting, etc.)
2. The entities involved (products, users, sales, etc.)
3. The time range if any
4. The aggregations needed if any
5. The appropriate database (MySQL for analytics, MongoDB for operations)

Question: {question}

Return a JSON object with the analysis.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.config.name,
                messages=[
                    {"role": "system", "content": "You are a query intent analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            self._track_usage(response.usage)

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            return {
                'type': 'unknown',
                'entities': [],
                'confidence': 0.0
            }

    async def validate_query(self,
                            query: str,
                            database_type: DatabaseType) -> tuple[bool, Optional[str]]:
        """
        Validate a generated query.

        Args:
            query: Query to validate
            database_type: Database type

        Returns:
            Tuple of (is_valid, error_message)
        """
        if database_type == DatabaseType.MYSQL:
            return self._validate_sql_query(query)
        else:
            return self._validate_mongodb_query(query)

    def _build_query_generation_prompt(self,
                                      database_type: DatabaseType,
                                      context: Optional[Dict[str, Any]]) -> str:
        """Build system prompt for query generation."""
        base_prompt = self.config.query_generation_prompt

        if database_type == DatabaseType.MYSQL:
            db_specific = """
You are generating MySQL queries. Focus on:
- Proper JOIN syntax
- GROUP BY for aggregations
- WHERE clauses for filtering
- ORDER BY for sorting
- LIMIT for result limiting
"""
        else:
            db_specific = """
You are generating MongoDB queries. Focus on:
- Proper filter syntax
- Aggregation pipelines when needed
- $match, $group, $sort stages
- Projection for field selection
- Limit for result limiting
"""

        # Add schema context if available
        schema_info = ""
        if context and 'schema' in context:
            schema_info = f"\nAvailable schema:\n{json.dumps(context['schema'], indent=2)}"

        return base_prompt + db_specific + schema_info

    def _build_answer_generation_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Build system prompt for answer generation."""
        base_prompt = self.config.answer_generation_prompt

        if context:
            if 'language' in context:
                base_prompt += f"\nRespond in {context['language']}."
            if 'format' in context:
                base_prompt += f"\nFormat the response as: {context['format']}"

        return base_prompt

    def _format_results_for_answer(self,
                                   question: str,
                                   results: List[Dict[str, Any]]) -> str:
        """Format query results for answer generation."""
        # Limit results for token efficiency
        limited_results = results[:50] if len(results) > 50 else results

        return f"""
Question: {question}

Query Results (showing {len(limited_results)} of {len(results)} total):
{json.dumps(limited_results, indent=2, ensure_ascii=False)}

Please provide a clear, concise answer to the question based on these results.
"""

    def _validate_sql_query(self, query: str) -> tuple[bool, Optional[str]]:
        """Validate SQL query for safety."""
        query_upper = query.upper().strip()

        # Check for dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE',
            'INSERT', 'UPDATE', 'REPLACE', 'GRANT', 'REVOKE'
        ]

        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False, f"Query contains forbidden operation: {keyword}"

        # Check for basic structure
        if not any(query_upper.startswith(kw) for kw in ['SELECT', 'WITH']):
            return False, "Query must be a SELECT statement"

        return True, None

    def _validate_mongodb_query(self, query: str) -> tuple[bool, Optional[str]]:
        """Validate MongoDB query for safety."""
        try:
            query_obj = json.loads(query) if isinstance(query, str) else query

            # Check for dangerous operations
            if not isinstance(query_obj, dict):
                return False, "Query must be a JSON object"

            # Ensure collection is specified
            if 'collection' not in query_obj:
                return False, "Collection name is required"

            # Check for write operations
            forbidden_ops = ['insert', 'update', 'delete', 'drop', 'create']
            for op in forbidden_ops:
                if op in str(query_obj).lower():
                    return False, f"Query contains forbidden operation: {op}"

            return True, None

        except json.JSONDecodeError:
            return False, "Invalid JSON query format"

    def _track_usage(self, usage):
        """Track token usage and costs."""
        if usage:
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            # Calculate cost
            input_cost = (input_tokens / 1000) * self.config.input_cost_per_1k
            output_cost = (output_tokens / 1000) * self.config.output_cost_per_1k
            total_cost = input_cost + output_cost

            # Update metrics
            self.total_requests += 1
            self.total_tokens_used += total_tokens
            self.total_cost_usd += total_cost
            self.last_request_tokens = total_tokens
            self.last_request_cost = total_cost

            logger.info(
                f"LLM usage: {total_tokens} tokens "
                f"(${total_cost:.4f}), "
                f"Total: ${self.total_cost_usd:.2f}"
            )

    def _track_streaming_usage(self, approximate_tokens: int, messages: List[Dict[str, str]]):
        """Track approximate usage for streaming responses."""
        # Estimate input tokens from messages
        input_tokens = sum(len(msg['content'].split()) * 1.3 for msg in messages)
        output_tokens = approximate_tokens * 1.3  # Rough approximation

        # Calculate approximate cost
        input_cost = (input_tokens / 1000) * self.config.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.config.output_cost_per_1k
        total_cost = input_cost + output_cost

        # Update metrics
        self.total_requests += 1
        self.total_tokens_used += int(input_tokens + output_tokens)
        self.total_cost_usd += total_cost

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get repository metrics.

        Returns:
            Dictionary with usage metrics
        """
        return {
            'total_requests': self.total_requests,
            'total_tokens_used': self.total_tokens_used,
            'total_cost_usd': self.total_cost_usd,
            'last_request_tokens': self.last_request_tokens,
            'last_request_cost': self.last_request_cost,
            'average_tokens_per_request': (
                self.total_tokens_used / self.total_requests
                if self.total_requests > 0 else 0
            ),
            'average_cost_per_request': (
                self.total_cost_usd / self.total_requests
                if self.total_requests > 0 else 0
            ),
            'model': self.config.name,
            'temperature': self.config.temperature
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"OpenAILLMRepository(model='{self.config.name}')"