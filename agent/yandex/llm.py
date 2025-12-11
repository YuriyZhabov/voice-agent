"""Yandex YandexGPT LLM plugin for LiveKit Agents.

Implements streaming chat completion using yandex_cloud_ml_sdk.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from livekit.agents import llm, APIConnectOptions
from livekit.agents.llm import ChatChunk, ChoiceDelta, FunctionToolCall

from agent.yandex.credentials import YandexCredentials

logger = logging.getLogger(__name__)


@dataclass
class _LLMOptions:
    """Internal options for LLM configuration."""
    model: str
    temperature: float
    max_tokens: int


class YandexLLM(llm.LLM):
    """YandexGPT LLM plugin for LiveKit Agents.
    
    Provides streaming chat completion using YandexGPT via yandex_cloud_ml_sdk.
    
    Example:
        >>> from agent.yandex import YandexCredentials
        >>> from agent.yandex.llm import YandexLLM
        >>> 
        >>> creds = YandexCredentials.from_env()
        >>> llm = YandexLLM(credentials=creds, model="yandexgpt-lite")
        >>> 
        >>> # Use in AgentSession
        >>> session = AgentSession(llm=llm, ...)
    """
    
    def __init__(
        self,
        *,
        credentials: YandexCredentials | None = None,
        model: str = "yandexgpt-lite",
        temperature: float = 0.6,
        max_tokens: int = 2000,
    ) -> None:
        """Initialize YandexLLM.
        
        Args:
            credentials: Yandex Cloud credentials (loads from env if None)
            model: Model name (yandexgpt-lite, yandexgpt, yandexgpt-32k)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in response
        """
        super().__init__()
        
        self._credentials = credentials or YandexCredentials.from_env()
        self._opts = _LLMOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._sdk = None
    
    def _get_sdk(self):
        """Lazy initialization of YCloudML SDK."""
        if self._sdk is None:
            try:
                from yandex_cloud_ml_sdk import YCloudML
            except ImportError as e:
                logger.error(
                    "Failed to import yandex_cloud_ml_sdk. "
                    "Run: pip install yandex-cloud-ml-sdk"
                )
                raise ImportError(
                    "yandex_cloud_ml_sdk not found. Install with: pip install yandex-cloud-ml-sdk"
                ) from e
            
            self._sdk = YCloudML(
                folder_id=self._credentials.folder_id,
                auth=self._credentials.api_key or self._credentials.iam_token,
            )
        return self._sdk
    
    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        conn_options: APIConnectOptions = APIConnectOptions(),
        fnc_ctx: llm.function_context.FunctionContext | None = None,
        temperature: float | None = None,
        n: int | None = None,
        parallel_tool_calls: bool | None = None,
        tool_choice: Any = None,
    ) -> "YandexLLMStream":
        """Generate chat completion.
        
        Args:
            chat_ctx: Chat context with message history
            conn_options: Connection options
            fnc_ctx: Function context with callable functions
            temperature: Ignored (uses instance setting)
            n: Ignored
            parallel_tool_calls: Ignored for Yandex
            tool_choice: Ignored for Yandex
        
        Returns:
            YandexLLMStream for streaming response
        """
        # Build tools list from fnc_ctx
        tools_list = []
        if fnc_ctx and fnc_ctx.ai_functions:
            tools_list = list(fnc_ctx.ai_functions.values())
        
        return YandexLLMStream(
            llm_instance=self,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            conn_options=conn_options,
            credentials=self._credentials,
            opts=self._opts,
            sdk_getter=self._get_sdk,
            tools_list=tools_list,
        )


def _convert_messages(chat_ctx: llm.ChatContext) -> list[dict[str, str]]:
    """Convert LiveKit ChatContext to YandexGPT message format."""
    messages = []
    
    # Get messages from ChatContext
    items = getattr(chat_ctx, 'items', None)
    if items is None:
        # Fallback to messages attribute
        items = getattr(chat_ctx, 'messages', [])
    
    for item in items:
        # Handle ChatMessage objects
        role = getattr(item, 'role', 'user')
        if hasattr(role, 'value'):
            role = role.value
        role = str(role)
        
        # Map LiveKit roles to YandexGPT roles
        if role in ("system", "developer"):
            yandex_role = "system"
        elif role == "user":
            yandex_role = "user"
        elif role == "assistant":
            yandex_role = "assistant"
        else:
            yandex_role = "user"
        
        # Extract text content
        content = ""
        item_content = getattr(item, 'content', None)
        
        if isinstance(item_content, str):
            content = item_content
        elif item_content is None:
            # Try to get text from item directly
            content = getattr(item, 'text', '') or ''
        elif isinstance(item_content, list):
            # Handle multi-part content
            for part in item_content:
                if isinstance(part, str):
                    content += part
                elif hasattr(part, 'text'):
                    content += part.text
        
        if content:
            messages.append({
                "role": yandex_role,
                "text": content,
            })
    
    return messages


def _convert_tools_to_yandex(tools_list: list) -> list[dict]:
    """Convert LiveKit FunctionTool list to YandexGPT tools format.
    
    YandexGPT expects tools in format:
    {
        "function": {
            "name": "tool_name",
            "description": "Tool description",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
    """
    import inspect
    
    if not tools_list:
        return []
    
    yandex_tools = []
    
    for tool in tools_list:
        # Get tool info from @function_tool decorator
        tool_info = getattr(tool, "__livekit_tool_info", None)
        if not tool_info:
            continue
        
        tool_name = tool_info.name
        tool_desc = tool_info.description or f"Function {tool_name}"
        
        # Build parameters from function signature
        properties = {}
        required = []
        
        # Get the actual function
        func = tool
        if hasattr(tool, "__wrapped__"):
            func = tool.__wrapped__
        
        try:
            sig = inspect.signature(func)
            type_hints = getattr(func, "__annotations__", {})
            
            for param_name, param in sig.parameters.items():
                # Skip context parameter
                if param_name in ("context", "self", "cls"):
                    continue
                
                param_schema = {"type": "string"}  # Default
                
                # Get type from annotations
                param_type = type_hints.get(param_name)
                if param_type:
                    type_name = getattr(param_type, "__name__", str(param_type))
                    if type_name in ("int", "integer"):
                        param_schema["type"] = "integer"
                    elif type_name in ("float", "number"):
                        param_schema["type"] = "number"
                    elif type_name in ("bool", "boolean"):
                        param_schema["type"] = "boolean"
                    elif type_name == "str":
                        param_schema["type"] = "string"
                
                param_schema["description"] = f"Parameter {param_name}"
                properties[param_name] = param_schema
                
                # If no default, it's required
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)
        except (ValueError, TypeError):
            pass
        
        yandex_tool = {
            "function": {
                "name": tool_name,
                "description": tool_desc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }
        yandex_tools.append(yandex_tool)
    
    return yandex_tools


class YandexLLMStream(llm.LLMStream):
    """Streaming LLM response from YandexGPT."""
    
    def __init__(
        self,
        *,
        llm_instance: YandexLLM,
        chat_ctx: llm.ChatContext,
        fnc_ctx: llm.function_context.FunctionContext | None,
        conn_options: APIConnectOptions,
        credentials: YandexCredentials,
        opts: _LLMOptions,
        sdk_getter,
        tools_list: list,
    ) -> None:
        super().__init__(llm=llm_instance, chat_ctx=chat_ctx, fnc_ctx=fnc_ctx, conn_options=conn_options)
        self._credentials = credentials
        self._opts = opts
        self._sdk_getter = sdk_getter
        self._tools_list = tools_list

    async def _run(self) -> None:
        """Stream tokens from YandexGPT."""
        sdk = self._sdk_getter()
        
        # Convert messages
        messages = _convert_messages(self._chat_ctx)
        
        logger.info(f"YandexGPT messages: {messages}")
        
        if not messages:
            logger.warning("No messages to send to YandexGPT")
            return
        
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Convert tools to YandexGPT format
            yandex_tools = _convert_tools_to_yandex(self._tools_list)
            
            if yandex_tools:
                logger.info(f"YandexGPT tools: {[t['function']['name'] for t in yandex_tools]}")
            
            # Use REST API for function calling support
            import httpx
            
            api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
            
            # Build request body
            request_body = {
                "modelUri": f"gpt://{self._credentials.folder_id}/{self._opts.model}",
                "completionOptions": {
                    "temperature": self._opts.temperature,
                    "maxTokens": str(self._opts.max_tokens),
                },
                "messages": messages,
            }
            
            # Add tools if available
            if yandex_tools:
                request_body["tools"] = yandex_tools
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self._credentials.api_key}",
                "x-folder-id": self._credentials.folder_id,
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, json=request_body, headers=headers)
                response.raise_for_status()
                result_data = response.json()
            
            logger.info(f"YandexGPT API result: {result_data}")
            
            # Process REST API result
            alternatives = result_data.get("result", {}).get("alternatives", [])
            
            for alternative in alternatives:
                message = alternative.get("message", {})
                
                # Check for tool calls (status = ALTERNATIVE_STATUS_TOOL_CALLS)
                tool_call_list = message.get("toolCallList", {})
                tool_calls = tool_call_list.get("toolCalls", [])
                
                if tool_calls:
                    logger.info(f"YandexGPT tool_calls: {tool_calls}")
                    
                    # Process each tool call - create FunctionToolCall objects
                    lk_tool_calls = []
                    for idx, tc in enumerate(tool_calls):
                        func_call = tc.get("functionCall", {})
                        func_name = func_call.get("name")
                        func_args = func_call.get("arguments", {})
                        
                        if func_name:
                            # Convert arguments to JSON string
                            if isinstance(func_args, dict):
                                args_str = json.dumps(func_args)
                            elif isinstance(func_args, str):
                                args_str = func_args
                            else:
                                args_str = "{}"
                            
                            # Create FunctionToolCall
                            tool_call = FunctionToolCall(
                                call_id=f"call_{request_id}_{idx}",
                                name=func_name,
                                arguments=args_str,
                            )
                            lk_tool_calls.append(tool_call)
                            logger.info(f"Created FunctionToolCall: {func_name}({args_str})")
                    
                    # Emit chunk with tool_calls
                    if lk_tool_calls:
                        chunk = ChatChunk(
                            id=request_id,
                            delta=ChoiceDelta(
                                role="assistant",
                                content=None,
                                tool_calls=lk_tool_calls,
                            ),
                        )
                        self._event_ch.send_nowait(chunk)
                        return  # Exit after emitting tool calls
                
                # Regular text response
                text = message.get("text", "")
                logger.info(f"YandexGPT response: {text[:100] if text else 'empty'}...")
                
                if text:
                    # Emit chunk with text content
                    chunk = ChatChunk(
                        id=request_id,
                        delta=ChoiceDelta(
                            role="assistant",
                            content=text,
                        ),
                    )
                    self._event_ch.send_nowait(chunk)
                    
        except Exception as e:
            logger.error(f"YandexGPT error: {e}", exc_info=True)
            raise
