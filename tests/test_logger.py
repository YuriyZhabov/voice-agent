"""Tests for CallLogger class.

Requirements: 6.1, 6.2, 6.3
"""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from agent.logger import CallLogger


class TestCallLoggerInit:
    """Tests for CallLogger initialization."""
    
    def test_init_sets_call_id(self, sample_call_id: str):
        """CallLogger should store the call_id."""
        logger = CallLogger(sample_call_id)
        assert logger.call_id == sample_call_id
    
    def test_init_sets_start_time(self, sample_call_id: str):
        """CallLogger should record start time on init."""
        before = datetime.now()
        logger = CallLogger(sample_call_id)
        after = datetime.now()
        
        assert before <= logger.start_time <= after
    
    def test_init_message_count_zero(self, sample_call_id: str):
        """CallLogger should start with zero message count."""
        logger = CallLogger(sample_call_id)
        assert logger.message_count == 0
    
    def test_init_tools_called_empty(self, sample_call_id: str):
        """CallLogger should start with empty tools list."""
        logger = CallLogger(sample_call_id)
        assert logger.tools_called == []


class TestLogEvent:
    """Tests for log_event method.
    
    Requirements: 6.1 - WHEN any event occurs during a call THEN the 
    Voice_Agent_MVP SHALL log the event with timestamp, call_id, and relevant data
    """
    
    def test_log_event_contains_timestamp(self, sample_call_id: str, caplog):
        """Log event should contain timestamp."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_event("test_event", {"key": "value"})
        
        log_entry = json.loads(caplog.records[-1].message)
        assert "timestamp" in log_entry
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(log_entry["timestamp"])
    
    def test_log_event_contains_call_id(self, sample_call_id: str, caplog):
        """Log event should contain call_id."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_event("test_event", {"key": "value"})
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["call_id"] == sample_call_id
    
    def test_log_event_contains_event_type(self, sample_call_id: str, caplog):
        """Log event should contain event type."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_event("custom_event", {"key": "value"})
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["event"] == "custom_event"
    
    def test_log_event_contains_data(self, sample_call_id: str, caplog):
        """Log event should contain event data."""
        logger = CallLogger(sample_call_id)
        data = {"key": "value", "number": 42}
        
        with caplog.at_level(logging.INFO):
            logger.log_event("test_event", data)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"] == data
    
    def test_log_event_with_none_data(self, sample_call_id: str, caplog):
        """Log event should handle None data."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_event("test_event")
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"] == {}


class TestLogMessage:
    """Tests for log_message method.
    
    Requirements: 6.1
    """
    
    def test_log_message_increments_count(self, sample_call_id: str, caplog):
        """log_message should increment message_count."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_message("user", "Hello")
            logger.log_message("assistant", "Hi there")
        
        assert logger.message_count == 2
    
    def test_log_message_contains_role(self, sample_call_id: str, caplog):
        """log_message should log the role."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_message("user", "Hello")
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"]["role"] == "user"
    
    def test_log_message_truncates_long_content(self, sample_call_id: str, caplog):
        """log_message should truncate content longer than 100 chars."""
        logger = CallLogger(sample_call_id)
        long_content = "x" * 150
        
        with caplog.at_level(logging.INFO):
            logger.log_message("user", long_content)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert len(log_entry["data"]["content"]) == 100
    
    def test_log_message_keeps_short_content(self, sample_call_id: str, caplog):
        """log_message should keep content shorter than 100 chars."""
        logger = CallLogger(sample_call_id)
        short_content = "Hello, world!"
        
        with caplog.at_level(logging.INFO):
            logger.log_message("user", short_content)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"]["content"] == short_content


class TestLogToolCall:
    """Tests for log_tool_call method.
    
    Requirements: 6.1
    """
    
    def test_log_tool_call_adds_to_list(self, sample_call_id: str, caplog):
        """log_tool_call should add tool name to tools_called list."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_tool_call("search_knowledge", True)
            logger.log_tool_call("create_order", False)
        
        assert logger.tools_called == ["search_knowledge", "create_order"]
    
    def test_log_tool_call_logs_success(self, sample_call_id: str, caplog):
        """log_tool_call should log success status."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_tool_call("my_tool", True)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"]["tool"] == "my_tool"
        assert log_entry["data"]["success"] is True
    
    def test_log_tool_call_logs_failure(self, sample_call_id: str, caplog):
        """log_tool_call should log failure status."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_tool_call("failing_tool", False)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"]["success"] is False


class TestLogError:
    """Tests for log_error method.
    
    Requirements: 6.3 - WHEN an error occurs THEN the Voice_Agent_MVP 
    SHALL log the error with stack trace and continue operation if possible
    """
    
    def test_log_error_contains_error_message(self, sample_call_id: str, caplog):
        """log_error should log the error message."""
        logger = CallLogger(sample_call_id)
        error = ValueError("Something went wrong")
        
        with caplog.at_level(logging.ERROR):
            logger.log_error(error)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["error"] == "Something went wrong"
    
    def test_log_error_contains_error_type(self, sample_call_id: str, caplog):
        """log_error should log the error type."""
        logger = CallLogger(sample_call_id)
        error = ValueError("Something went wrong")
        
        with caplog.at_level(logging.ERROR):
            logger.log_error(error)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["type"] == "ValueError"
    
    def test_log_error_contains_stack_trace(self, sample_call_id: str, caplog):
        """log_error should include stack trace."""
        logger = CallLogger(sample_call_id)
        error = RuntimeError("Test error")
        
        with caplog.at_level(logging.ERROR):
            logger.log_error(error)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert "stack_trace" in log_entry
    
    def test_log_error_contains_call_id(self, sample_call_id: str, caplog):
        """log_error should include call_id."""
        logger = CallLogger(sample_call_id)
        error = Exception("Test")
        
        with caplog.at_level(logging.ERROR):
            logger.log_error(error)
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["call_id"] == sample_call_id


class TestLogSummary:
    """Tests for log_summary method.
    
    Requirements: 6.2 - WHEN a call ends THEN the Voice_Agent_MVP SHALL 
    log a summary with duration, message count, and tools called
    """
    
    def test_log_summary_contains_duration(self, sample_call_id: str, caplog):
        """log_summary should include call duration."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_summary()
        
        log_entry = json.loads(caplog.records[-1].message)
        assert "duration_seconds" in log_entry["data"]
        assert log_entry["data"]["duration_seconds"] >= 0
    
    def test_log_summary_contains_message_count(self, sample_call_id: str, caplog):
        """log_summary should include message count."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_message("user", "Hello")
            logger.log_message("assistant", "Hi")
            logger.log_summary()
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"]["message_count"] == 2
    
    def test_log_summary_contains_tools_called(self, sample_call_id: str, caplog):
        """log_summary should include tools called."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_tool_call("tool1", True)
            logger.log_tool_call("tool2", False)
            logger.log_summary()
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["data"]["tools_called"] == ["tool1", "tool2"]
    
    def test_log_summary_event_type(self, sample_call_id: str, caplog):
        """log_summary should use 'call_ended' event type."""
        logger = CallLogger(sample_call_id)
        
        with caplog.at_level(logging.INFO):
            logger.log_summary()
        
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["event"] == "call_ended"
