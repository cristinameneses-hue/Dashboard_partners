"""
Streaming Query Use Case

Handles streaming responses for real-time user experience.
Follows Interface Segregation Principle with specialized streaming interface.
"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import json

from domain.entities import Query, User, Conversation
from domain.repositories import DatabaseRepository, LLMRepository
from domain.value_objects import DatabaseType, QueryResult
from .execute_query import ExecuteQueryUseCase


logger = logging.getLogger(__name__)


class StreamingQueryUseCase:
    """
    Use case for executing queries with streaming responses.

    Extends ExecuteQueryUseCase to provide real-time streaming
    of query results and answer generation.
    """

    def __init__(self,
                 execute_query_use_case: ExecuteQueryUseCase,
                 llm_repository: Optional[LLMRepository] = None):
        """
        Initialize streaming query use case.

        Args:
            execute_query_use_case: Base query execution use case
            llm_repository: LLM repository with streaming support
        """
        self.execute_query_use_case = execute_query_use_case
        self.llm_repository = llm_repository

        # Metrics
        self.total_streams = 0
        self.active_streams = 0
        self.total_tokens_streamed = 0

    async def execute_stream(self,
                            question: str,
                            user: Optional[User] = None,
                            conversation: Optional[Conversation] = None,
                            context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute query with streaming response.

        Yields events in the format:
        {
            "type": "status" | "token" | "result" | "error" | "done",
            "content": <data>,
            "metadata": {...}
        }

        Args:
            question: Natural language question
            user: User executing the query
            conversation: Current conversation
            context: Additional context

        Yields:
            Stream events as dictionaries

        Raises:
            ValueError: If validation fails
            RuntimeError: If execution fails
        """
        self.total_streams += 1
        self.active_streams += 1
        stream_id = f"stream_{datetime.now().timestamp()}"

        try:
            # Yield initial status
            yield {
                "type": "status",
                "content": "Iniciando análisis de consulta...",
                "metadata": {
                    "stream_id": stream_id,
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Create query entity
            query = Query(
                question=question,
                user_id=user.id if user else None,
                session_id=conversation.id if conversation else None
            )

            # Step 1: Validate user
            if user:
                yield {
                    "type": "status",
                    "content": "Validando permisos de usuario..."
                }
                self.execute_query_use_case._validate_user_permissions(user, query)

            # Step 2: Analyze intent
            yield {
                "type": "status",
                "content": "Analizando intención de la consulta..."
            }
            query = await self.execute_query_use_case._analyze_intent(query, context)

            if query.intent:
                yield {
                    "type": "metadata",
                    "content": {
                        "intent_type": query.intent.type.value,
                        "confidence": query.intent.confidence,
                        "entities": [e.value for e in query.intent.entities]
                    }
                }

            # Step 3: Route query
            yield {
                "type": "status",
                "content": "Determinando base de datos apropiada..."
            }
            query = await self.execute_query_use_case._route_query(query, context)

            database_name = "MySQL" if query.database_type == DatabaseType.MYSQL else "MongoDB"
            yield {
                "type": "metadata",
                "content": {
                    "database": database_name,
                    "confidence": query.routing_decision.confidence
                }
            }

            # Step 4: Generate query
            yield {
                "type": "status",
                "content": f"Generando consulta para {database_name}..."
            }
            query = await self.execute_query_use_case._generate_query(query, context)

            # Step 5: Execute query
            yield {
                "type": "status",
                "content": "Ejecutando consulta en base de datos..."
            }
            query = await self.execute_query_use_case._execute_database_query(query)

            # Yield result summary
            if query.result and query.result.is_success:
                yield {
                    "type": "result",
                    "content": {
                        "count": query.result.count,
                        "execution_time_ms": query.result.execution_time_ms,
                        "database": database_name
                    }
                }
            else:
                yield {
                    "type": "error",
                    "content": "Error ejecutando consulta en base de datos"
                }

            # Step 6: Stream answer generation
            yield {
                "type": "status",
                "content": "Generando respuesta..."
            }

            # Check if LLM supports streaming
            if self.llm_repository and hasattr(self.llm_repository, 'generate_stream'):
                # Prepare messages for streaming
                messages = self._prepare_messages_for_streaming(
                    query,
                    conversation,
                    context
                )

                # Stream tokens
                token_count = 0
                async for token in self.llm_repository.generate_stream(messages, context):
                    yield {
                        "type": "token",
                        "content": token
                    }
                    token_count += 1
                    self.total_tokens_streamed += 1

                # Store complete answer
                # Note: In production, we'd accumulate tokens
                query.natural_language_answer = f"[Streamed {token_count} tokens]"

            else:
                # Fallback to non-streaming answer
                query = await self.execute_query_use_case._generate_answer(query, context)

                # Simulate streaming by yielding in chunks
                answer = query.natural_language_answer
                chunk_size = 50  # Characters per chunk

                for i in range(0, len(answer), chunk_size):
                    chunk = answer[i:i + chunk_size]
                    yield {
                        "type": "token",
                        "content": chunk
                    }
                    await asyncio.sleep(0.01)  # Small delay for streaming effect

            # Complete query
            query.complete_execution(
                result=query.result,
                natural_language_answer=query.natural_language_answer
            )

            # Update user metrics
            if user:
                await self.execute_query_use_case._update_user_metrics(user, query)

            # Update conversation
            if conversation:
                conversation.add_query(query.id)
                conversation.add_message("user", question)
                conversation.add_message("assistant", query.natural_language_answer)

            # Yield completion
            yield {
                "type": "done",
                "content": "Consulta completada",
                "metadata": {
                    "query_id": query.id,
                    "total_time_ms": query.total_execution_time_ms,
                    "cost_usd": query.actual_cost or query.estimated_cost or 0.0
                }
            }

        except Exception as e:
            logger.error(f"Streaming query failed: {str(e)}")
            yield {
                "type": "error",
                "content": str(e),
                "metadata": {
                    "stream_id": stream_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            raise

        finally:
            self.active_streams -= 1

    async def execute_chat_stream(self,
                                 message: str,
                                 conversation: Conversation,
                                 user: Optional[User] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute chat-style query with conversation context.

        Optimized for ChatGPT-style interactions with conversation history.

        Args:
            message: User message
            conversation: Active conversation
            user: User in conversation

        Yields:
            Stream events
        """
        # Add user message to conversation
        conversation.add_message("user", message)

        # Check if this is a follow-up or new query
        is_followup = self._is_followup_query(message, conversation)

        if is_followup:
            # Handle as conversation continuation
            yield {
                "type": "status",
                "content": "Continuando conversación..."
            }

            # Stream direct LLM response without database query
            messages = conversation.get_messages_for_llm(max_messages=10)

            if self.llm_repository and hasattr(self.llm_repository, 'generate_stream'):
                token_buffer = []
                async for token in self.llm_repository.generate_stream(messages):
                    yield {
                        "type": "token",
                        "content": token
                    }
                    token_buffer.append(token)

                # Store complete response
                complete_response = ''.join(token_buffer)
                conversation.add_message("assistant", complete_response)

            else:
                # Fallback to non-streaming
                response = await self.llm_repository.generate_answer(
                    message,
                    [],  # No database results for follow-up
                    {"conversation_history": messages}
                )

                for chunk in self._chunk_text(response):
                    yield {
                        "type": "token",
                        "content": chunk
                    }

                conversation.add_message("assistant", response)

            yield {
                "type": "done",
                "content": "Respuesta completada"
            }

        else:
            # Handle as new database query
            async for event in self.execute_stream(
                message,
                user,
                conversation,
                {"is_chat": True}
            ):
                yield event

    def _prepare_messages_for_streaming(self,
                                       query: Query,
                                       conversation: Optional[Conversation],
                                       context: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Prepare messages for LLM streaming.

        Args:
            query: Query with results
            conversation: Optional conversation context
            context: Additional context

        Returns:
            List of messages for LLM
        """
        messages = []

        # Add system prompt
        system_prompt = """
Eres un asistente experto en análisis de datos.
Tu tarea es explicar los resultados de consultas de base de datos de forma clara y útil.
Responde siempre en español.
"""
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history if available
        if conversation:
            # Get recent messages (limit to avoid token overflow)
            history = conversation.get_messages_for_llm(max_messages=6)
            messages.extend(history[1:])  # Skip system prompt from history

        # Add current query context
        query_context = f"""
Pregunta: {query.question}
Base de datos consultada: {query.database_type.value}
Resultados obtenidos: {query.result.count if query.result else 0} registros
"""

        # Add results summary (limited to avoid token overflow)
        if query.result and query.result.data:
            results_preview = query.result.data[:10]  # First 10 results
            query_context += f"\nPrimeros resultados:\n{json.dumps(results_preview, indent=2, ensure_ascii=False)}"

        messages.append({"role": "user", "content": query_context})

        return messages

    def _is_followup_query(self, message: str, conversation: Conversation) -> bool:
        """
        Determine if message is a follow-up query.

        Args:
            message: User message
            conversation: Current conversation

        Returns:
            True if this is a follow-up, False if new query
        """
        # Simple heuristics for follow-up detection
        followup_indicators = [
            '?',  # Questions
            'explica', 'explicar', 'explain',
            'más', 'more', 'detalle', 'detail',
            'por qué', 'why', 'cómo', 'how',
            'también', 'also', 'además',
            'y ', 'and '
        ]

        message_lower = message.lower()

        # Check if message is short and contains follow-up indicators
        if len(message.split()) < 10:
            for indicator in followup_indicators:
                if indicator in message_lower:
                    return True

        # Check if message references previous context
        if conversation.total_messages > 2:
            # Has conversation history
            last_assistant_message = None
            for msg in reversed(conversation.messages):
                if msg.role == "assistant":
                    last_assistant_message = msg.content
                    break

            if last_assistant_message:
                # Check for references to previous response
                if any(word in message_lower for word in ['eso', 'esto', 'that', 'this']):
                    return True

        return False

    def _chunk_text(self, text: str, chunk_size: int = 50) -> List[str]:
        """
        Split text into chunks for simulated streaming.

        Args:
            text: Text to chunk
            chunk_size: Characters per chunk

        Returns:
            List of text chunks
        """
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get streaming metrics.

        Returns:
            Metrics dictionary
        """
        base_metrics = await self.execute_query_use_case.get_metrics()

        return {
            **base_metrics,
            'total_streams': self.total_streams,
            'active_streams': self.active_streams,
            'total_tokens_streamed': self.total_tokens_streamed,
            'average_tokens_per_stream': (
                self.total_tokens_streamed / self.total_streams
                if self.total_streams > 0 else 0
            )
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"StreamingQueryUseCase("
            f"total_streams={self.total_streams}, "
            f"active={self.active_streams}"
            f")"
        )