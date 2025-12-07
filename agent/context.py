"""Conversation context management for Voice Agent MVP.

This module provides classes for managing conversation history and context
that is passed to the LLM for response generation.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """A single message in the conversation.
    
    Attributes:
        role: The role of the message sender ('user' or 'assistant')
        content: The text content of the message
        timestamp: When the message was created
    """
    role: str  # 'user' | 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationContext:
    """Manages conversation history with automatic trimming.
    
    Keeps track of messages exchanged during a call and provides
    methods to format the context for LLM consumption.
    
    Attributes:
        call_id: Unique identifier for the call
        messages: List of messages in the conversation
        max_messages: Maximum number of messages to retain (default: 5)
        system_prompt: System instructions for the LLM (optional)
    """
    call_id: str
    messages: list[Message] = field(default_factory=list)
    max_messages: int = 5
    system_prompt: str | None = None
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message and trim to max_messages.
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The text content of the message
        """
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_context_for_llm(self) -> list[dict]:
        """Return messages in LLM-compatible format.
        
        Returns:
            List of dictionaries with 'role' and 'content' keys,
            suitable for passing to OpenAI-compatible LLM APIs.
            If system_prompt is set, it is included as the first message.
        """
        result = []
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        result.extend(
            {"role": m.role, "content": m.content}
            for m in self.messages
        )
        return result
    
    def clear(self) -> None:
        """Clear all messages from the context."""
        self.messages = []
    
    def __len__(self) -> int:
        """Return the number of messages in the context."""
        return len(self.messages)
