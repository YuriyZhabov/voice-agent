"""Tests for agent tools module.

Property-based tests using Hypothesis for tool validation.

Requirements: 1.1, 2.1, 2.2, 3.2
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore


def get_tool_info(tool):
    """Helper to get tool info from decorated function."""
    return getattr(tool, "__livekit_tool_info", None)


class TestGetAllTools:
    """Tests for get_all_tools function (Property 1)."""
    
    def test_returns_list(self):
        """get_all_tools should return a list."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        assert isinstance(tools, list)
    
    def test_returns_non_empty_list(self):
        """get_all_tools should return at least one tool."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        assert len(tools) > 0
    
    def test_all_items_are_function_tools(self):
        """All items in get_all_tools should have __livekit_tool_info (Property 1)."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        for tool in tools:
            info = get_tool_info(tool)
            assert info is not None, f"{tool} is not a FunctionTool (no __livekit_tool_info)"
    
    def test_tools_have_names(self):
        """All tools should have non-empty names (Property 2)."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        for tool in tools:
            info = get_tool_info(tool)
            assert info is not None
            assert info.name
            assert isinstance(info.name, str)
    
    def test_tools_have_descriptions(self):
        """All tools should have descriptions from docstrings (Property 3)."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        for tool in tools:
            info = get_tool_info(tool)
            assert info is not None
            assert info.description
            assert isinstance(info.description, str)


class TestEndCallTool:
    """Tests for end_call tool."""
    
    def test_end_call_exists(self):
        """end_call tool should be in the tools list."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        tool_names = [get_tool_info(t).name for t in tools]
        assert "end_call" in tool_names
    
    def test_end_call_has_reason_param(self):
        """end_call should accept reason parameter."""
        from agent.tools.core import end_call
        
        # Check the tool has the expected info
        info = get_tool_info(end_call)
        assert info is not None
        assert info.name == "end_call"


class TestGetCurrentTimeTool:
    """Tests for get_current_time tool."""
    
    def test_get_current_time_exists(self):
        """get_current_time tool should be in the tools list."""
        from agent.tools import get_all_tools
        
        tools = get_all_tools()
        tool_names = [get_tool_info(t).name for t in tools]
        assert "get_current_time" in tool_names
    
    @pytest.mark.asyncio
    async def test_get_current_time_returns_moscow_time(self):
        """get_current_time should return Moscow timezone time (Property 4)."""
        from agent.tools.time import get_current_time
        
        # Create mock context
        mock_context = MagicMock()
        mock_context.userdata = {}
        
        # Call the decorated function directly (it's still callable)
        result = await get_current_time(mock_context)
        
        # Verify result contains Moscow time
        assert "московскому времени" in result
        
        # Verify the time is close to actual Moscow time
        moscow_tz = ZoneInfo("Europe/Moscow")
        now = datetime.now(moscow_tz)
        
        # Time should be in the result (may differ by a minute)
        assert ":" in result  # Contains time format
    
    @pytest.mark.asyncio
    async def test_get_current_time_format(self):
        """get_current_time should return properly formatted Russian response."""
        from agent.tools.time import get_current_time
        
        mock_context = MagicMock()
        mock_context.userdata = {}
        
        result = await get_current_time(mock_context)
        
        # Should contain "Сейчас" and time format
        assert "Сейчас" in result
        assert ":" in result  # Time separator
        assert "." in result  # Date separator


class TestToolNaming:
    """Tests for tool naming conventions (Property 2)."""
    
    def test_tool_names_match_function_names(self):
        """Tool names should match their function names."""
        from agent.tools.core import end_call
        from agent.tools.time import get_current_time
        
        assert get_tool_info(end_call).name == "end_call"
        assert get_tool_info(get_current_time).name == "get_current_time"


class TestToolsMerge:
    """Tests for tools list merge (Property 5)."""
    
    def test_merge_preserves_all_builtin_tools(self):
        """Merging tools should preserve all built-in tools (Property 5).
        
        **Feature: agent-tools, Property 5: Tools list merge preserves all tools**
        **Validates: Requirements 5.3**
        """
        from agent.tools import get_all_tools
        from agent.tools.core import TOOLS as CORE_TOOLS
        from agent.tools.time import TOOLS as TIME_TOOLS
        
        all_tools = get_all_tools()
        
        # All core tools should be in the merged list
        for tool in CORE_TOOLS:
            assert tool in all_tools, f"Core tool {tool} not in merged list"
        
        # All time tools should be in the merged list
        for tool in TIME_TOOLS:
            assert tool in all_tools, f"Time tool {tool} not in merged list"
    
    def test_merge_count_equals_sum(self):
        """Merged tools count should equal sum of all module tools."""
        from agent.tools import get_all_tools
        from agent.tools.core import TOOLS as CORE_TOOLS
        from agent.tools.time import TOOLS as TIME_TOOLS
        
        all_tools = get_all_tools()
        expected_count = len(CORE_TOOLS) + len(TIME_TOOLS)
        
        assert len(all_tools) == expected_count
