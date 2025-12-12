"""Universal tool executor for YandexGPT function calling.

Provides a centralized way to execute tools from any LLM integration.
Handles tool discovery, validation, and execution with proper error handling.
"""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


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
        
        try:
            # Execute the tool - first arg is always context
            result = await tool_func(context, **arguments)
            
            # Convert result to string for LLM
            result_str = str(result) if result is not None else "OK"
            
            logger.info(f"Tool {name} completed: {result_str[:200]}...")
            return result_str
            
        except TypeError as e:
            # Handle missing/extra arguments
            error_msg = f"Invalid arguments for {name}: {e}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"
            
        except Exception as e:
            # Handle any other errors
            error_msg = f"Tool {name} failed: {e}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"
    
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
