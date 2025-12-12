"""Agent tools module.

Provides a unified interface for all agent tools.
Auto-imports all tool modules and exposes get_all_tools() function.

Requirements: 1.1, 1.2, 1.3
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from livekit.agents import FunctionTool

logger = logging.getLogger(__name__)

# Import all tool modules
from agent.tools.core import TOOLS as CORE_TOOLS
from agent.tools.time import TOOLS as TIME_TOOLS
from agent.tools.weather import TOOLS as WEATHER_TOOLS


def _get_tool_name(tool: "FunctionTool") -> str:
    """Get tool name from FunctionTool (decorated function)."""
    info = getattr(tool, "__livekit_tool_info", None)
    if info:
        return info.name
    return getattr(tool, "__name__", "unknown")


def get_all_tools() -> list["FunctionTool"]:
    """Return all registered tools for the agent.
    
    Collects tools from all tool modules and returns them as a list.
    
    Returns:
        List of FunctionTool objects ready to be passed to Agent constructor.
    """
    all_tools = []
    
    # Collect tools from all modules
    all_tools.extend(CORE_TOOLS)
    all_tools.extend(TIME_TOOLS)
    all_tools.extend(WEATHER_TOOLS)
    
    tool_names = [_get_tool_name(t) for t in all_tools]
    logger.info(f"Loaded {len(all_tools)} tools: {tool_names}")
    
    return all_tools


from agent.tools.executor import ToolExecutor, get_executor, reset_executor
from agent.tools.models import (
    FunctionCall,
    FunctionResult,
    ToolCall,
    ToolResult,
    ToolCallList,
    ToolResultList,
)

__all__ = [
    # Tool discovery
    "get_all_tools",
    "_get_tool_name",
    # Executor
    "ToolExecutor",
    "get_executor",
    "reset_executor",
    # Pydantic models
    "FunctionCall",
    "FunctionResult",
    "ToolCall",
    "ToolResult",
    "ToolCallList",
    "ToolResultList",
]
