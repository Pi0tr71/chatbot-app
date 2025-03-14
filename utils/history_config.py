from enum import StrEnum
import json
import os
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

HISTORY_PATH = Path("json_files/chat_history.json")


class ContentType(StrEnum):
    """Enum representing content types in messages."""

    TEXT = "text"
    IMAGE_URL = "image_url"


class ImageDetail(StrEnum):
    """Enum for image detail levels."""

    LOW = "low"
    HIGH = "high"


class TextContent(BaseModel):
    """Model for text content."""

    type: Literal[ContentType.TEXT] = ContentType.TEXT
    text: str


class ImageUrlContent(BaseModel):
    """Model for image URL content."""

    type: Literal[ContentType.IMAGE_URL] = ContentType.IMAGE_URL
    image_url: Dict[str, Union[str, ImageDetail]]


class FileContent(BaseModel):  # Maybe will be changed in future
    """Model for file content."""

    type: Literal[ContentType.TEXT]
    text: str


# Union type for all possible content types
ContentItem = Union[TextContent, ImageUrlContent, FileContent]


class MessageRole(StrEnum):
    """Enum for message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Model for a chat message."""

    role: MessageRole
    content: List[ContentItem]
    tokens_used: Optional[int] = 0
    reasoning_tokens: Optional[int] = 0
    cost: Optional[float] = 0.0
    provider: Optional[str] = None
    model: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    throughput: Optional[float] = 0.0
    response_time: Optional[float] = 0.0

    def format_timestamp(self) -> str:
        """Format the timestamp as string."""
        return self.timestamp.strftime("%d-%m-%Y %H:%M:%S")


class Chat(BaseModel):
    """Model for a chat session."""

    chat_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    chat_name: str
    messages: List[Message] = Field(default_factory=list)
    last_active: datetime = Field(default_factory=lambda: datetime.now())
    additional_params: Dict[str, Any] = Field(default_factory=dict)

    def format_last_active(self) -> str:
        """Format the last active timestamp as string."""
        return self.last_active.strftime("%d-%m-%Y %H:%M")

    def add_message(self, message: Message) -> None:
        """Add a new message to the chat."""
        self.messages.append(message)
        self.last_active = datetime.now()


class ChatHistory(BaseModel):
    """Model for storing multiple chats."""

    chats: Dict[str, Chat] = Field(default_factory=dict)

    def add_chat(self, chat: Chat) -> None:
        """Add a new chat to the history."""
        self.chats[chat.chat_id] = chat

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by its ID."""
        return self.chats.get(chat_id)

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by its ID."""
        if chat_id in self.chats:
            del self.chats[chat_id]
            self.save_to_file()
            return True
        return False

    def save_to_file(self, path: str = None) -> None:
        """Save chat history to a JSON file."""
        file_path = path if path is not None else HISTORY_PATH
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, path: str = None) -> "ChatHistory":
        """Load chat history from a JSON file."""
        file_path = path if path is not None else HISTORY_PATH
        if not os.path.exists(file_path):
            return cls()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return cls.model_validate(data)
