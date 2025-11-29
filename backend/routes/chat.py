import asyncio
from typing import List, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from backend.services.chat import get_chat_manager


class ChatMessageModel(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description="User message content to send to the agent.",
        min_length=1,
    )
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation identifier, if continuing a chat."
    )


class ChatResponse(BaseModel):
    conversation_id: str
    messages: List[ChatMessageModel]
    latest_message: Optional[ChatMessageModel] = None


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the chat agent",
)
async def post_chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the agent and get a response."""
    manager = get_chat_manager()
    conversation_id, session = manager.get_or_create(request.conversation_id)

    # Send message and get response
    response_message = await asyncio.to_thread(session.send, request.message)

    # Get all messages from the session
    all_messages = await asyncio.to_thread(session.get_messages)

    return ChatResponse(
        conversation_id=conversation_id,
        messages=[ChatMessageModel(**message) for message in all_messages],
        latest_message=ChatMessageModel(
            **response_message) if response_message else None,
    )


@router.get(
    "/{conversation_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve chat history",
)
async def get_chat(conversation_id: str) -> ChatResponse:
    manager = get_chat_manager()
    session = manager.get(conversation_id)

    all_messages = await asyncio.to_thread(session.get_messages)
    latest_message = (
        ChatMessageModel(**all_messages[-1]) if all_messages else None
    )
    return ChatResponse(
        conversation_id=conversation_id,
        messages=[ChatMessageModel(**message) for message in all_messages],
        latest_message=latest_message,
    )
