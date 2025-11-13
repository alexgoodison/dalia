import json
from typing import List, Optional

from agno.agent import RunEvent, RunOutputEvent
import anyio
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from queue import Queue
import threading

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


async def _stream_chat_response(request: ChatRequest):
    """Async generator that streams agent output using SSE."""

    manager = get_chat_manager()
    conversation_id, session = manager.get_or_create(request.conversation_id)

    # Notify client with conversation id
    yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"

    events: Queue[Optional[RunOutputEvent]] = Queue()

    def _run_stream() -> None:
        try:
            stream = session.stream(request.message)
            for event in stream:
                events.put(event)
        finally:
            events.put(None)

    producer = threading.Thread(target=_run_stream, daemon=True)
    producer.start()

    try:
        while True:
            event = await anyio.to_thread.run_sync(events.get)
            if not event:
                break

            if event.event == RunEvent.run_content:
                chunk = str(event.content) if event.content else ""
                if chunk:
                    yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
            elif event.event == RunEvent.run_error:
                error_msg = (
                    str(getattr(event, "error", None))
                    if getattr(event, "error", None)
                    else "An error occurred while generating a response."
                )
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                return
            elif event.event == RunEvent.run_completed:
                break

        messages = await anyio.to_thread.run_sync(session.get_messages)
        yield f"data: {json.dumps({'type': 'complete', 'conversation_id': conversation_id, 'messages': messages})}\n\n"
    finally:
        producer.join(timeout=0)


@router.post("/stream")
async def post_chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream chat responses using Server-Sent Events (SSE)."""
    return StreamingResponse(
        _stream_chat_response(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
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

    all_messages = await anyio.to_thread.run_sync(session.get_messages)
    latest_message = (
        ChatMessageModel(**all_messages[-1]) if all_messages else None
    )
    return ChatResponse(
        conversation_id=conversation_id,
        messages=[ChatMessageModel(**message) for message in all_messages],
        latest_message=latest_message,
    )
