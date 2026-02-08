"""
Chat API routes for conversational todo management.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services import chat_service, conversation_service


router = APIRouter()


# Request/Response Schemas

class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's natural language message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to resume existing conversation")


class ToolCall(BaseModel):
    """Schema for tool call information."""
    tool: str = Field(..., description="Name of the tool invoked")
    arguments: dict = Field(..., description="Arguments passed to the tool")
    result: dict = Field(..., description="Result returned by the tool")


class ChatResponseData(BaseModel):
    """Data schema for successful chat response."""
    conversation_id: str = Field(..., description="Conversation identifier")
    response: str = Field(..., description="AI-generated response")
    tool_calls: list[ToolCall] = Field(default_factory=list, description="List of tool calls executed")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[ChatResponseData] = Field(None, description="Response data")
    message: str = Field(..., description="Status message")


class ConversationItem(BaseModel):
    """Schema for conversation list item."""
    id: str
    user_id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class ConversationsResponseData(BaseModel):
    """Data schema for conversations list response."""
    conversations: list[ConversationItem]
    total: int


class ConversationsResponse(BaseModel):
    """Response schema for conversations list endpoint."""
    success: bool
    data: ConversationsResponseData
    message: str


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    error: ErrorDetail


# API Endpoints

@router.post(
    "/{user_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message to AI chat agent",
    description="Send a natural language message to the AI agent for todo management"
)
async def chat(
    user_id: UUID,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Send a message to the AI chat agent.

    The agent will:
    1. Understand the user's intent
    2. Invoke appropriate MCP tools (create, list, update, delete todos)
    3. Return a friendly conversational response

    **Stateless Design**: Server reconstructs full conversation context from database on every request.

    **Authentication**: Requires valid JWT token. User ID in token must match user_id in path.
    """
    # Verify user_id matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You don't have permission to access this user's chat",
                "details": {}
            }
        )

    # Validate and parse conversation_id if provided
    conversation_uuid = None
    if request.conversation_id:
        try:
            conversation_uuid = UUID(request.conversation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_INPUT",
                    "message": "Invalid conversation ID format",
                    "details": {"conversation_id": request.conversation_id}
                }
            )

    # Process message with AI agent
    result = await chat_service.process_message(
        session=session,
        user_id=user_id,
        message=request.message,
        conversation_id=conversation_uuid
    )

    # Handle errors
    if not result.get("success"):
        error_message = result.get("error", "An unexpected error occurred")

        # Determine appropriate status code
        if "not found" in error_message.lower() or "access denied" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
            error_code = "NOT_FOUND"
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_code = "INTERNAL_ERROR"

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": error_code,
                "message": error_message,
                "details": {}
            }
        )

    # Return successful response
    return ChatResponse(
        success=True,
        data=ChatResponseData(
            conversation_id=result["conversation_id"],
            response=result["response"],
            tool_calls=[
                ToolCall(
                    tool=tc["tool"],
                    arguments=tc["arguments"],
                    result=tc["result"]
                )
                for tc in result.get("tool_calls", [])
            ]
        ),
        message="Message processed successfully"
    )


@router.get(
    "/{user_id}/conversations",
    response_model=ConversationsResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's conversations",
    description="Retrieve a list of all conversations for the authenticated user"
)
async def list_conversations(
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all conversations for the authenticated user.

    Conversations are ordered by most recently updated first.
    """
    # Verify user_id matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You don't have permission to access this user's conversations",
                "details": {}
            }
        )

    # Validate pagination parameters
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_INPUT",
                "message": "Limit must be between 1 and 100",
                "details": {"limit": limit}
            }
        )

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_INPUT",
                "message": "Offset must be non-negative",
                "details": {"offset": offset}
            }
        )

    # Get conversations
    conversations = await conversation_service.list_conversations(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset
    )

    # Format response
    return ConversationsResponse(
        success=True,
        data=ConversationsResponseData(
            conversations=[
                ConversationItem(
                    id=str(conv.id),
                    user_id=str(conv.user_id),
                    title=conv.title,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat()
                )
                for conv in conversations
            ],
            total=len(conversations)
        ),
        message="Conversations retrieved successfully"
    )
