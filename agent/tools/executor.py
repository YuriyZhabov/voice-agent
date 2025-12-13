"""Universal tool executor for YandexGPT function calling.

Provides a centralized way to execute tools from any LLM integration.
Handles tool discovery, validation, and execution with proper error handling.
"""

import asyncio
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Import Supabase logging (lazy to avoid circular imports)
_supabase_log_tool = None

def _get_supabase_log_tool():
    global _supabase_log_tool
    if _supabase_log_tool is None:
        try:
            from agent.supabase_client import log_tool_execution
            _supabase_log_tool = log_tool_execution
        except ImportError:
            _supabase_log_tool = lambda *args, **kwargs: asyncio.sleep(0)
    return _supabase_log_tool


class ToolExecutor:
    """Universal executor for LiveKit function tools.
    
    Provides:
    - Tool registration and discovery
    - Safe execution with error handling
    - Support for async tools
    - Logging and debugging
    
    Example:
        >>> from agent.tools import get_all_tools
        >>> from agent.tools.executor import ToolExecutor
        >>> 
        >>> executor = ToolExecutor(get_all_tools())
        >>> result = await executor.execute("get_weather", {"city": "Москва"})
    """
    
    def __init__(self, tools: list | None = None) -> None:
        """Initialize executor with optional tools list.
        
        Args:
            tools: List of @function_tool decorated functions.
                   If None, will auto-load from agent.tools.get_all_tools()
        """
        self._tools_map: dict[str, Callable] = {}
        self._tools_info: dict[str, dict] = {}
        
        if tools is None:
            from agent.tools import get_all_tools
            tools = get_all_tools()
        
        self._register_tools(tools)
    
    def _register_tools(self, tools: list) -> None:
        """Register tools from a list of @function_tool decorated functions."""
        for tool in tools:
            tool_info = getattr(tool, "__livekit_tool_info", None)
            if tool_info:
                name = tool_info.name
                self._tools_map[name] = tool
                self._tools_info[name] = {
                    "name": name,
                    "description": tool_info.description,
                    "function": tool,
                }
                logger.debug(f"Registered tool: {name}")
        
        logger.info(f"ToolExecutor initialized with {len(self._tools_map)} tools: {list(self._tools_map.keys())}")
    
    def register(self, tool: Callable) -> None:
        """Register a single tool dynamically.
        
        Args:
            tool: A @function_tool decorated function
        """
        tool_info = getattr(tool, "__livekit_tool_info", None)
        if not tool_info:
            raise ValueError(f"Tool must be decorated with @function_tool: {tool}")
        
        name = tool_info.name
        self._tools_map[name] = tool
        self._tools_info[name] = {
            "name": name,
            "description": tool_info.description,
            "function": tool,
        }
        logger.info(f"Dynamically registered tool: {name}")
    
    def get_tool(self, name: str) -> Callable | None:
        """Get a tool function by name."""
        return self._tools_map.get(name)
    
    def get_tool_names(self) -> list[str]:
        """Get list of all registered tool names."""
        return list(self._tools_map.keys())
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools_map
    
    async def execute(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        context: Any = None,
    ) -> str:
        """Execute a tool by name with given arguments.
        
        Args:
            name: Tool name to execute
            arguments: Dictionary of arguments to pass to the tool
            context: Optional RunContext (can be None for tools that don't need it)
        
        Returns:
            String result from the tool (for LLM consumption)
        
        Raises:
            ValueError: If tool is not found
        """
        if not self.has_tool(name):
            error_msg = f"Tool not found: {name}. Available: {self.get_tool_names()}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        tool_func = self._tools_map[name]
        arguments = arguments or {}
        
        logger.info(f"Executing tool: {name}({arguments})")
        
        start_time = time.time()
        success = True
        result_str = ""
        
        try:
            # Execute the tool - first arg is always context
            result = await tool_func(context, **arguments)
            
            # Convert result to string for LLM
            result_str = str(result) if result is not None else "OK"
            
            logger.info(f"Tool {name} completed: {result_str[:200]}...")
            return result_str
            
        except TypeError as e:
            # Handle missing/extra arguments
            success = False
            error_msg = f"Invalid arguments for {name}: {e}"
            logger.error(error_msg, exc_info=True)
            result_str = f"Error: {error_msg}"
            return result_str
            
        except Exception as e:
            # Handle any other errors
            success = False
            error_msg = f"Tool {name} failed: {e}"
            logger.error(error_msg, exc_info=True)
            result_str = f"Error: {error_msg}"
            return result_str
        
        finally:
            # Log to Supabase (fire and forget)
            latency_ms = int((time.time() - start_time) * 1000)
            # Extract call_id from context if available
            call_id = None
            if context and hasattr(context, "userdata"):
                call_id = context.userdata.get("room_name")
            if call_id:
                log_func = _get_supabase_log_tool()
                asyncio.create_task(log_func(
                    call_id=call_id,
                    tool_name=name,
                    parameters=arguments,
                    result={"value": result_str[:500]},
                    success=success,
                    latency_ms=latency_ms,
                ))
    
    async def execute_batch(
        self,
        tool_calls: list[dict],
        context: Any = None,
    ) -> list[dict]:
        """Execute multiple tool calls and return results.
        
        Args:
            tool_calls: List of tool calls in YandexGPT format:
                [{"functionCall": {"name": "...", "arguments": {...}}}]
            context: Optional RunContext
        
        Returns:
            List of results in YandexGPT toolResultList format:
                [{"functionResult": {"name": "...", "content": "..."}}]
        """
        results = []
        
        for tc in tool_calls:
            func_call = tc.get("functionCall", {})
            name = func_call.get("name")
            arguments = func_call.get("arguments", {})
            
            if name:
                result = await self.execute(name, arguments, context)
                results.append({
                    "functionResult": {
                        "name": name,
                        "content": result,
                    }
                })
        
        return results


# Global executor instance (lazy initialization)
_global_executor: ToolExecutor | None = None


def get_executor() -> ToolExecutor:
    """Get or create the global ToolExecutor instance.
    
    Returns:
        Singleton ToolExecutor with all registered tools
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = ToolExecutor()
    return _global_executor


def reset_executor() -> None:
    """Reset the global executor (useful for testing)."""
    global _global_executor
    _global_executor = None
