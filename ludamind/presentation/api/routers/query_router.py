"""
Query Router

API endpoints for executing database queries with natural language.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from ..dependencies import get_current_user, get_container
from ..schemas.query_schemas import (
    QueryRequest,
    QueryResponse,
    QueryStreamRequest,
    QueryAnalysisResponse
)
from ....domain.entities.query import Query
from ....domain.entities.user import User
from ....infrastructure.di.container import Container

router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> QueryResponse:
    """
    Execute a natural language query against the databases.

    This endpoint analyzes the query, routes it to the appropriate database
    (MySQL or MongoDB), executes it, and returns formatted results.

    Args:
        request: Query request with natural language text
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        QueryResponse with results and metadata

    Raises:
        HTTPException: On query execution errors
    """
    try:
        # Get use case from container
        execute_query_use_case = container.execute_query_use_case()

        # Create query entity
        query = Query(
            text=request.query,
            user_id=current_user.id if current_user else None,
            session_id=request.session_id,
            metadata={
                "source": "api",
                "use_chatgpt": request.use_chatgpt,
                "force_database": request.force_database
            }
        )

        # Execute query
        result = await execute_query_use_case.execute(
            query=query,
            use_cache=request.use_cache,
            timeout_seconds=request.timeout_seconds
        )

        # Schedule background analytics
        background_tasks.add_task(
            log_query_analytics,
            query_id=result.query_id,
            user_id=current_user.id if current_user else None,
            execution_time_ms=result.execution_time_ms
        )

        # Return response
        return QueryResponse(
            query_id=result.query_id,
            query=request.query,
            results=result.data,
            formatted_response=result.formatted_response,
            database_used=result.database_used,
            execution_time_ms=result.execution_time_ms,
            from_cache=result.from_cache,
            metadata={
                "routing_confidence": result.routing_confidence,
                "matched_keywords": result.matched_keywords,
                "result_count": len(result.data) if result.data else 0
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail="Query execution timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Query execution failed")


@router.post("/stream")
async def execute_streaming_query(
    request: QueryStreamRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
):
    """
    Execute a streaming query with Server-Sent Events.

    This endpoint executes a query and streams the response as it's generated,
    providing real-time feedback to the user.

    Args:
        request: Streaming query request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        StreamingResponse with SSE events
    """
    async def generate():
        """Generate streaming events."""
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Processing query...'})}\n\n"

            # Get streaming use case from container
            streaming_use_case = container.streaming_query_use_case()

            # Create query entity
            query = Query(
                text=request.query,
                user_id=current_user.id if current_user else None,
                session_id=request.session_id,
                metadata={"source": "api_streaming"}
            )

            # Execute with streaming
            async for chunk in streaming_use_case.execute_streaming(query):
                event_data = {
                    "type": chunk.type,
                    "content": chunk.content,
                    "metadata": chunk.metadata
                }
                yield f"data: {json.dumps(event_data)}\n\n"

                # Small delay for demonstration
                await asyncio.sleep(0.01)

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Query completed'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/analyze", response_model=QueryAnalysisResponse)
async def analyze_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> QueryAnalysisResponse:
    """
    Analyze a query without executing it.

    This endpoint analyzes the query to determine routing, complexity,
    and other metadata without actually executing it.

    Args:
        request: Query request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        QueryAnalysisResponse with analysis results
    """
    try:
        # Get router service from container
        query_router = container.query_router_service()

        # Create query entity
        query = Query(
            text=request.query,
            user_id=current_user.id if current_user else None
        )

        # Route query
        routing_decision = query_router.route_query(query)

        # Analyze complexity
        complexity = query_router.analyze_query_complexity(query)

        # Get explanation
        explanation = query_router.get_routing_explanation(query)

        return QueryAnalysisResponse(
            query=request.query,
            routing={
                "database": routing_decision.primary_database.value,
                "confidence": routing_decision.confidence,
                "reasoning": routing_decision.reasoning,
                "matched_keywords": list(routing_decision.matched_keywords.values()),
                "alternative_database": routing_decision.alternative_database.value if routing_decision.alternative_database else None,
                "needs_confirmation": routing_decision.needs_confirmation
            },
            complexity=complexity,
            explanation=explanation,
            estimated_execution_time_ms=_estimate_execution_time(complexity)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> QueryResponse:
    """
    Get query details by ID.

    Retrieve a previously executed query by its ID.

    Args:
        query_id: Query identifier
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        QueryResponse with query details

    Raises:
        HTTPException: If query not found or access denied
    """
    try:
        # Get query repository from container
        query_repository = container.query_repository()

        # Retrieve query
        query = await query_repository.get_by_id(query_id)

        if not query:
            raise HTTPException(status_code=404, detail="Query not found")

        # Check authorization
        if query.user_id and query.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return QueryResponse(
            query_id=query.id,
            query=query.text,
            results=query.results.data if query.results else [],
            formatted_response=query.results.formatted_response if query.results else None,
            database_used=query.database_used.value if query.database_used else None,
            execution_time_ms=query.execution_time_ms,
            from_cache=query.cache_hit,
            metadata={
                "created_at": query.created_at.isoformat() if query.created_at else None,
                "processed_at": query.processed_at.isoformat() if query.processed_at else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve query")


@router.get("/")
async def list_queries(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> list[QueryResponse]:
    """
    List queries for the current user.

    Get a paginated list of queries executed by the current user.

    Args:
        limit: Maximum number of queries to return
        offset: Number of queries to skip
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        List of QueryResponse objects
    """
    try:
        # Get query repository from container
        query_repository = container.query_repository()

        # Retrieve queries
        queries = await query_repository.get_by_user(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )

        # Convert to response format
        return [
            QueryResponse(
                query_id=query.id,
                query=query.text,
                results=query.results.data[:10] if query.results else [],  # Truncate
                formatted_response=None,  # Don't include full response in list
                database_used=query.database_used.value if query.database_used else None,
                execution_time_ms=query.execution_time_ms,
                from_cache=query.cache_hit,
                metadata={
                    "created_at": query.created_at.isoformat() if query.created_at else None
                }
            )
            for query in queries
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list queries")


# Helper functions

async def log_query_analytics(
    query_id: str,
    user_id: Optional[str],
    execution_time_ms: int
):
    """
    Background task to log query analytics.

    Args:
        query_id: Query identifier
        user_id: User identifier
        execution_time_ms: Query execution time
    """
    # TODO: Implement analytics logging
    pass


def _estimate_execution_time(complexity: Dict[str, Any]) -> int:
    """
    Estimate query execution time based on complexity.

    Args:
        complexity: Query complexity analysis

    Returns:
        Estimated execution time in milliseconds
    """
    base_time = 100  # Base time in ms

    if complexity.get("estimated_difficulty") == "high":
        base_time *= 10
    elif complexity.get("estimated_difficulty") == "medium":
        base_time *= 5

    if complexity.get("requires_aggregation"):
        base_time *= 2

    if complexity.get("is_complex"):
        base_time *= 3

    return base_time