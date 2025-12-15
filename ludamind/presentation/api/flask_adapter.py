"""
Flask Adapter - Bridge between Flask and Clean Architecture
Minimal viable adapter following Interface Adapter pattern
"""

from flask import Flask, request, jsonify, Response, session
from typing import Dict, Any, Optional
import asyncio
import json
import logging
from functools import wraps

from domain.use_cases import ExecuteQueryUseCase, StreamingQueryUseCase
from domain.entities import User, Conversation
from infrastructure.di.container import DIContainer

logger = logging.getLogger(__name__)

class FlaskAdapter:
    """Adapter to connect Flask with domain use cases."""

    def __init__(self, app: Flask, container: DIContainer):
        self.app = app
        self.container = container
        self._setup_routes()

    def _setup_routes(self):
        """Configure Flask routes."""
        self.app.route('/api/query', methods=['POST'])(self.query_endpoint)
        self.app.route('/api/query_stream', methods=['POST'])(self.query_stream_endpoint)
        self.app.route('/api/chat', methods=['POST'])(self.chat_endpoint)
        self.app.route('/api/health', methods=['GET'])(self.health_endpoint)

    def require_auth(self, f):
        """Authentication decorator."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            return f(*args, **kwargs)
        return decorated

    @require_auth
    def query_endpoint(self):
        """Execute query endpoint."""
        try:
            data = request.json
            question = data.get('question')
            use_chatgpt = data.get('use_chatgpt', False)

            if not question:
                return jsonify({'error': 'Question is required'}), 400

            # Get use case from container
            use_case = self.container.get_execute_query_use_case(use_chatgpt)

            # Get current user from session
            user = self._get_current_user()

            # Execute query asynchronously
            query = asyncio.run(use_case.execute(question, user))

            return jsonify({
                'answer': query.natural_language_answer,
                'database': query.database_type.value if query.database_type else None,
                'count': query.result.count if query.result else 0,
                'execution_time_ms': query.total_execution_time_ms,
                'query_id': query.id
            })

        except Exception as e:
            logger.error(f"Query endpoint error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @require_auth
    def query_stream_endpoint(self):
        """Streaming query endpoint."""
        try:
            data = request.json
            question = data.get('question')
            use_chatgpt = data.get('use_chatgpt', False)

            if not question:
                return jsonify({'error': 'Question is required'}), 400

            # Get streaming use case
            use_case = self.container.get_streaming_query_use_case(use_chatgpt)
            user = self._get_current_user()
            conversation = self._get_or_create_conversation()

            def generate():
                """Generate SSE events."""
                async def run_stream():
                    async for event in use_case.execute_stream(
                        question, user, conversation
                    ):
                        yield f"data: {json.dumps(event)}\n\n"

                # Run async generator in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    for event in loop.run_until_complete(run_stream()):
                        yield event
                finally:
                    loop.close()

            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )

        except Exception as e:
            logger.error(f"Stream endpoint error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @require_auth
    def chat_endpoint(self):
        """ChatGPT-style chat endpoint."""
        try:
            data = request.json
            message = data.get('message')
            conversation_id = data.get('conversation_id')

            if not message:
                return jsonify({'error': 'Message is required'}), 400

            # Get ChatGPT use case
            use_case = self.container.get_chatgpt_use_case()
            user = self._get_current_user()

            # Get or create conversation
            if conversation_id:
                conversation = self.container.get_conversation_repository().get(conversation_id)
            else:
                conversation = Conversation(user_id=user.id if user else None)

            # Execute in chat mode
            query = asyncio.run(
                use_case.execute(message, user, conversation, {'mode': 'chat'})
            )

            return jsonify({
                'response': query.natural_language_answer,
                'conversation_id': conversation.id,
                'query_id': query.id,
                'cost_usd': query.actual_cost or query.estimated_cost or 0.0
            })

        except Exception as e:
            logger.error(f"Chat endpoint error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    def health_endpoint(self):
        """Health check endpoint."""
        try:
            # Check database connections
            mysql_ok = self.container.test_mysql_connection()
            mongodb_ok = self.container.test_mongodb_connection()

            return jsonify({
                'status': 'healthy' if (mysql_ok and mongodb_ok) else 'degraded',
                'services': {
                    'mysql': mysql_ok,
                    'mongodb': mongodb_ok
                }
            })
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

    def _get_current_user(self) -> Optional[User]:
        """Get current user from session."""
        if 'user_id' in session:
            # In production, load from repository
            return User(
                id=session['user_id'],
                username=session.get('username', 'user'),
                email=session.get('email', 'user@example.com')
            )
        return None

    def _get_or_create_conversation(self) -> Conversation:
        """Get or create conversation from session."""
        if 'conversation_id' not in session:
            conversation = Conversation(
                user_id=session.get('user_id')
            )
            session['conversation_id'] = conversation.id
        else:
            # In production, load from repository
            conversation = Conversation(
                id=session['conversation_id'],
                user_id=session.get('user_id')
            )
        return conversation