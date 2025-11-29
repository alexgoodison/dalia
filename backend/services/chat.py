from functools import lru_cache
from threading import Lock
from typing import Dict, List, Literal, Optional, TypedDict
from uuid import uuid4

from agno.agent import Agent, RunOutput

from backend.services.agent import dalia_agent

ChatRole = Literal["user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


class ChatSession:
    agent: Agent
    conversation_id: str

    def __init__(self, agent: Agent, conversation_id: str) -> None:
        self.agent = agent
        self.conversation_id = conversation_id

    def send(self, content: str) -> ChatMessage:
        result: RunOutput = self.agent.run(
            content,
            session_id=self.conversation_id,
            add_history_to_context=True,
        )

        response_content = result.content
        if isinstance(response_content, list):
            response_text = "".join(str(part) for part in response_content)
        else:
            response_text = str(response_content)

        response: ChatMessage = ChatMessage(
            role="assistant", content=response_text)
        return response

    def get_messages(self) -> List[ChatMessage]:
        """Get all messages from the Agno session."""
        try:
            agno_messages = self.agent.get_messages_for_session(
                session_id=self.conversation_id
            )
            messages: List[ChatMessage] = []
            for msg in agno_messages:
                if not (msg.role == "assistant" or msg.role == "user") or not msg.content:
                    continue

                messages.append(ChatMessage(
                    role=msg.role, content=str(msg.content)))
            return messages
        except Exception:
            return []


@lru_cache(maxsize=1)
def _manager() -> "ChatSessionManager":
    return ChatSessionManager()


class ChatSessionManager:
    def __init__(self) -> None:
        self._agent = dalia_agent
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = Lock()

    def _new_session(self) -> tuple[str, ChatSession]:
        conversation_id = str(uuid4())
        session = ChatSession(
            agent=self._agent, conversation_id=conversation_id)
        self._sessions[conversation_id] = session
        return conversation_id, session

    def get_or_create(self, conversation_id: Optional[str]) -> tuple[str, ChatSession]:
        with self._lock:
            if conversation_id:
                session = self._sessions.get(conversation_id)
                if session is None:
                    # Create a new session wrapper for existing Agno session
                    session = ChatSession(
                        agent=self._agent, conversation_id=conversation_id)
                    self._sessions[conversation_id] = session
                return conversation_id, session

            conversation_id, session = self._new_session()
            return conversation_id, session

    def get(self, conversation_id: str) -> ChatSession:
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session is None:
                # Create a new session wrapper for existing Agno session
                session = ChatSession(
                    agent=self._agent, conversation_id=conversation_id)
                self._sessions[conversation_id] = session
            return session


def get_chat_manager() -> ChatSessionManager:
    return _manager()
