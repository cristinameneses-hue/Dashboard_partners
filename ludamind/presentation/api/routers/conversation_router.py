"""
Conversation Router

API endpoints for managing conversations and chat interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import asyncio
from datetime import datetime

from ..dependencies import get_current_user, get_container
from ..schemas.conversation_schemas import (
    CreateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
    ConversationMessageRequest,
    UpdateConversationRequest,
    ConversationContextRequest,
    ConversationContextResponse,
    GenerateTitleRequest,
    GenerateTitleResponse,
    ExportConversationRequest,
    ConversationStatistics,
    ConversationMessage
)
from ..schemas.common_schemas import SuccessResponse
from ....domain.entities.user import User
from ....infrastructure.di.container import Container

router = APIRouter()


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationResponse:
    """
    Create a new conversation.

    Creates a new conversation session with optional initial message.

    Args:
        request: Conversation creation request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationResponse with created conversation details

    Raises:
        HTTPException: On creation errors
    """
    try:
        # Get conversation manager from container
        conversation_manager = container.conversation_manager_use_case()

        # Create conversation
        conversation = await conversation_manager.create_conversation(
            user_id=current_user.id if current_user else None,
            title=request.title,
            metadata=request.metadata
        )

        # Add initial message if provided
        if request.initial_message:
            await conversation_manager.add_user_message(
                conversation_id=conversation.id,
                content=request.initial_message
            )

        # Convert to response format
        return _conversation_to_response(conversation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    only_active: bool = True,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationListResponse:
    """
    List conversations for the current user.

    Get a paginated list of conversations for the authenticated user.

    Args:
        page: Page number (1-based)
        page_size: Items per page
        only_active: Filter for active conversations only
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationListResponse with paginated conversations
    """
    try:
        # Get conversation manager from container
        conversation_manager = container.conversation_manager_use_case()

        # Calculate offset
        offset = (page - 1) * page_size

        # Get conversations
        conversations = await conversation_manager.get_user_conversations(
            user_id=current_user.id,
            limit=page_size,
            offset=offset,
            only_active=only_active
        )

        # Get total count (simplified - in production, add a count method)
        total_count = len(conversations)  # TODO: Implement proper count

        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1

        # Convert to response format
        return ConversationListResponse(
            conversations=[_conversation_to_response(conv) for conv in conversations],
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationResponse:
    """
    Get conversation details.

    Retrieve a specific conversation by ID.

    Args:
        conversation_id: Conversation identifier
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationResponse with conversation details

    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        # Get conversation manager from container
        conversation_manager = container.conversation_manager_use_case()

        # Get conversation
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check authorization
        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return _conversation_to_response(conversation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.post("/{conversation_id}/messages", response_model=ConversationResponse)
async def add_message(
    conversation_id: str,
    request: ConversationMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationResponse:
    """
    Add a message to conversation.

    Add a user message to an existing conversation and get AI response.

    Args:
        conversation_id: Conversation identifier
        request: Message request
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationResponse with updated conversation

    Raises:
        HTTPException: On message processing errors
    """
    try:
        # Get conversation manager from container
        conversation_manager = container.conversation_manager_use_case()

        # Verify conversation exists and user has access
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Add user message
        await conversation_manager.add_user_message(
            conversation_id=conversation_id,
            content=request.content,
            metadata=request.metadata
        )

        # Get query execution use case
        query_use_case = container.execute_query_use_case()

        # Get conversation context for processing
        context = await conversation_manager.get_conversation_context(conversation_id)

        # Execute query with context
        from ....domain.entities.query import Query
        query = Query(
            text=request.content,
            user_id=current_user.id,
            conversation_id=conversation_id
        )

        result = await query_use_case.execute(
            query=query,
            conversation_context=context
        )

        # Add assistant response
        await conversation_manager.add_assistant_response(
            conversation_id=conversation_id,
            content=result.formatted_response,
            token_count=result.token_count,
            cost_usd=result.cost_usd,
            metadata={"database_used": result.database_used}
        )

        # Get updated conversation
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        # Schedule background analytics
        background_tasks.add_task(
            log_message_analytics,
            conversation_id=conversation_id,
            user_id=current_user.id
        )

        return _conversation_to_response(conversation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.post("/{conversation_id}/messages/stream")
async def add_message_streaming(
    conversation_id: str,
    request: ConversationMessageRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
):
    """
    Add a message with streaming response.

    Add a user message and stream the AI response using Server-Sent Events.

    Args:
        conversation_id: Conversation identifier
        request: Message request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        StreamingResponse with SSE events
    """
    async def generate():
        """Generate streaming events."""
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Processing message...'})}\n\n"

            # Get conversation manager
            conversation_manager = container.conversation_manager_use_case()

            # Verify access
            conversation = await conversation_manager.get_conversation_by_id(conversation_id)
            if not conversation:
                yield f"data: {json.dumps({'type': 'error', 'error': 'Conversation not found'})}\n\n"
                return

            if conversation.user_id and conversation.user_id != current_user.id:
                yield f"data: {json.dumps({'type': 'error', 'error': 'Access denied'})}\n\n"
                return

            # Add user message
            await conversation_manager.add_user_message(
                conversation_id=conversation_id,
                content=request.content,
                metadata=request.metadata
            )

            # Get streaming use case
            streaming_use_case = container.streaming_query_use_case()

            # Create query
            from ....domain.entities.query import Query
            query = Query(
                text=request.content,
                user_id=current_user.id,
                conversation_id=conversation_id
            )

            # Stream response
            response_text = ""
            async for chunk in streaming_use_case.execute_streaming(query):
                response_text += chunk.content
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                await asyncio.sleep(0.01)

            # Save assistant response
            await conversation_manager.add_assistant_response(
                conversation_id=conversation_id,
                content=response_text
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Response complete'})}\n\n"

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


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationResponse:
    """
    Update conversation details.

    Update title, status, or metadata of a conversation.

    Args:
        conversation_id: Conversation identifier
        request: Update request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationResponse with updated conversation

    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        # Get conversation manager
        conversation_manager = container.conversation_manager_use_case()

        # Get conversation
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update fields
        if request.title is not None:
            conversation.title = request.title

        if request.is_active is not None:
            if request.is_active:
                conversation.reactivate()
            else:
                conversation.archive()

        if request.metadata is not None:
            conversation.metadata.update(request.metadata)

        # Save updates
        conversation_repository = container.conversation_repository()
        await conversation_repository.save(conversation)

        return _conversation_to_response(conversation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")


@router.delete("/{conversation_id}", response_model=SuccessResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> SuccessResponse:
    """
    Delete a conversation.

    Permanently delete a conversation and all its messages.

    Args:
        conversation_id: Conversation identifier
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        SuccessResponse indicating deletion status

    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        # Get conversation manager
        conversation_manager = container.conversation_manager_use_case()

        # Verify ownership
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete conversation
        success = await conversation_manager.delete_conversation(conversation_id)

        return SuccessResponse(
            success=success,
            message="Conversation deleted successfully" if success else "Failed to delete conversation"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/{conversation_id}/title", response_model=GenerateTitleResponse)
async def generate_title(
    conversation_id: str,
    request: GenerateTitleRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> GenerateTitleResponse:
    """
    Generate a title for conversation.

    Use AI to generate an appropriate title based on conversation content.

    Args:
        conversation_id: Conversation identifier
        request: Title generation request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        GenerateTitleResponse with generated title

    Raises:
        HTTPException: On generation errors
    """
    try:
        # Get conversation manager
        conversation_manager = container.conversation_manager_use_case()

        # Verify ownership
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Generate title
        title = await conversation_manager.generate_title(conversation_id)

        return GenerateTitleResponse(
            title=title,
            confidence=0.85  # TODO: Calculate actual confidence
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate title: {str(e)}")


@router.get("/{conversation_id}/context", response_model=ConversationContextResponse)
async def get_conversation_context(
    conversation_id: str,
    request: ConversationContextRequest = Depends(),
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationContextResponse:
    """
    Get conversation context for LLM.

    Retrieve formatted conversation context suitable for LLM interaction.

    Args:
        conversation_id: Conversation identifier
        request: Context request parameters
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationContextResponse with formatted context

    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        # Get conversation manager
        conversation_manager = container.conversation_manager_use_case()

        # Verify ownership
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get context
        context = await conversation_manager.get_conversation_context(
            conversation_id=conversation_id,
            max_messages=request.max_messages
        )

        # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
        total_chars = sum(len(msg["content"]) for msg in context)
        token_estimate = total_chars // 4

        return ConversationContextResponse(
            context=context,
            message_count=len(context),
            has_summary=conversation.summary is not None,
            token_estimate=token_estimate
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.post("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    request: ExportConversationRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
):
    """
    Export conversation in various formats.

    Export conversation content in JSON, Markdown, Text, or CSV format.

    Args:
        conversation_id: Conversation identifier
        request: Export request
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        File response with exported conversation

    Raises:
        HTTPException: If conversation not found or export fails
    """
    try:
        # Get conversation manager
        conversation_manager = container.conversation_manager_use_case()

        # Verify ownership
        conversation = await conversation_manager.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Export conversation
        exported_content = await conversation_manager.export_conversation(
            conversation_id=conversation_id,
            format=request.format
        )

        # Set appropriate content type
        content_types = {
            "json": "application/json",
            "markdown": "text/markdown",
            "text": "text/plain",
            "csv": "text/csv"
        }
        content_type = content_types.get(request.format, "text/plain")

        # Set filename
        filename = f"conversation_{conversation_id}.{request.format}"

        return Response(
            content=exported_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export conversation: {str(e)}")


@router.get("/statistics/user", response_model=ConversationStatistics)
async def get_user_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container)
) -> ConversationStatistics:
    """
    Get conversation statistics for the current user.

    Retrieve statistics about user's conversations over a time period.

    Args:
        days: Number of days to include in statistics
        current_user: Authenticated user
        container: Dependency injection container

    Returns:
        ConversationStatistics with user's stats
    """
    try:
        # Get conversation manager
        conversation_manager = container.conversation_manager_use_case()

        # Get user conversations
        conversations = await conversation_manager.get_user_conversations(
            user_id=current_user.id,
            limit=1000,  # Get all conversations for stats
            offset=0,
            only_active=False
        )

        # Calculate statistics
        total_conversations = len(conversations)
        active_conversations = sum(1 for c in conversations if c.is_active)
        total_messages = sum(len(c.messages) for c in conversations)
        total_tokens = sum(c.token_count for c in conversations)
        total_cost = sum(c.total_cost_usd for c in conversations)

        avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

        # Calculate average duration
        durations = []
        for conv in conversations:
            duration = conv.get_duration()
            if duration:
                durations.append(duration.total_seconds())

        avg_duration = sum(durations) / len(durations) if durations else 0

        from datetime import timedelta
        period_start = datetime.utcnow() - timedelta(days=days)
        period_end = datetime.utcnow()

        return ConversationStatistics(
            total_conversations=total_conversations,
            active_conversations=active_conversations,
            total_messages=total_messages,
            average_messages_per_conversation=avg_messages,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            average_conversation_duration_seconds=avg_duration,
            period={"start": period_start, "end": period_end}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# Helper functions

def _conversation_to_response(conversation) -> ConversationResponse:
    """Convert domain conversation entity to response model."""
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        messages=[
            ConversationMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
                token_count=msg.token_count,
                cost_usd=msg.cost_usd
            )
            for msg in conversation.messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
        is_active=conversation.is_active,
        token_count=conversation.token_count,
        total_cost_usd=conversation.total_cost_usd,
        metadata=conversation.metadata,
        summary=conversation.summary,
        user_id=conversation.user_id
    )


async def log_message_analytics(conversation_id: str, user_id: str):
    """Background task to log message analytics."""
    # TODO: Implement analytics logging
    pass