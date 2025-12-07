"""
Structured logging for call events.

Requirements: 6.1, 6.2, 6.3
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any


class CallLogger:
    """Structured logging for call events.
    
    Provides methods for logging call events, messages, tool calls,
    errors, and call summaries with consistent formatting.
    
    Attributes:
        call_id: Unique identifier for the call
        start_time: When the call started
        message_count: Number of messages logged
        tools_called: List of tool names that were called
    """
    
    def __init__(self, call_id: str):
        """Initialize CallLogger for a specific call.
        
        Args:
            call_id: Unique identifier for the call
        """
        self.call_id = call_id
        self.start_time = datetime.now()
        self.message_count = 0
        self.tools_called: list[str] = []
        self.logger = logging.getLogger(f"call.{call_id}")
        
        # Ensure logger has at least INFO level
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Log an event with timestamp and call_id.
        
        Args:
            event_type: Type of event (e.g., 'message', 'tool_call', 'call_started')
            data: Optional dictionary with event-specific data
            
        Requirements: 6.1 - WHEN any event occurs during a call THEN the 
        Voice_Agent_MVP SHALL log the event with timestamp, call_id, and relevant data
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "call_id": self.call_id,
            "event": event_type,
            "data": data or {}
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_message(self, role: str, content: str) -> None:
        """Log a conversation message.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content (truncated to 100 chars in log)
            
        Requirements: 6.1
        """
        self.message_count += 1
        self.log_event("message", {
            "role": role,
            "content": content[:100] if len(content) > 100 else content
        })
    
    def log_tool_call(self, tool_name: str, success: bool) -> None:
        """Log a tool execution.
        
        Args:
            tool_name: Name of the tool that was called
            success: Whether the tool execution was successful
            
        Requirements: 6.1
        """
        self.tools_called.append(tool_name)
        self.log_event("tool_call", {
            "tool": tool_name,
            "success": success
        })
    
    def log_error(self, error: Exception) -> None:
        """Log an error with stack trace.
        
        Args:
            error: The exception that occurred
            
        Requirements: 6.3 - WHEN an error occurs THEN the Voice_Agent_MVP 
        SHALL log the error with stack trace and continue operation if possible
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "call_id": self.call_id,
            "event": "error",
            "error": str(error),
            "type": type(error).__name__,
            "stack_trace": traceback.format_exc()
        }
        self.logger.error(json.dumps(error_entry), exc_info=True)
    
    def log_summary(self) -> None:
        """Log call summary on end.
        
        Requirements: 6.2 - WHEN a call ends THEN the Voice_Agent_MVP SHALL 
        log a summary with duration, message count, and tools called
        """
        duration = (datetime.now() - self.start_time).total_seconds()
        self.log_event("call_ended", {
            "duration_seconds": duration,
            "message_count": self.message_count,
            "tools_called": self.tools_called
        })
