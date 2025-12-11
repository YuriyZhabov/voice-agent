"""Yandex YandexGPT LLM plugin for LiveKit Agents.

Implements streaming chat completion using yandex_cloud_ml_sdk.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from livekit.agents import llm

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
        tools: list[llm.FunctionTool] | None = None,
        tool_choice: llm.ToolChoice = "auto",
    ) -> YandexLLMStream:
        """Generate chat completion.
        
        Args:
            chat_ctx: Chat context with message history
            tools: Optional list of function tools
            tool_choice: Tool selection mode
        
        Returns:
            YandexLLMStream for streaming response
        """
        return YandexLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools,
            tool_choice=tool_choice,
            credentials=self._credentials,
            opts=self._opts,
            sdk_getter=self._get_sdk,
        )


def _convert_messages(chat_ctx: llm.ChatContext) -> list[dict[str, str]]:
    """Convert LiveKit ChatContext to YandexGPT message format."""
    messages = []
    
    for msg in chat_ctx.messages:
        role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
        
        # Map LiveKit roles to YandexGPT roles
        if role in ("system", "developer"):
            yandex_role = "system"
        elif role == "user":
            yandex_role = "user"
        elif role == "assistant":
            yandex_role = "assistant"
        else:
            yandex_role = "user"  # Default fallback
        
        # Extract text content
        content = ""
        if isinstance(msg.content, str):
            content = msg.content
        elif isinstance(msg.content, list):
            # Handle multi-part content
            for part in msg.content:
                if hasattr(part, 'text'):
                    content += part.text
                elif isinstance(part, str):
                    content += part
        
        if content:
            messages.append({
                "role": yandex_role,
                "text": content,
            })
    
    return messages


def _convert_tools(tools: list[llm.FunctionTool] | None) -> list[dict[str, Any]] | None:
    """Convert LiveKit FunctionTools to YandexGPT function format."""
    if not tools:
        return None
    
    yandex_tools = []
    for tool in tools:
        func_def = {
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.parameters if hasattr(tool, 'parameters') else {
                    "type": "object",
                    "properties": {},
                },
            }
        }
        yandex_tools.append(func_def)
    
    return yandex_tools


class YandexLLMStream(llm.LLMStream):
    """Streaming LLM response from YandexGPT."""
    
    def __init__(
        self,
        *,
        llm: YandexLLM,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool] | None,
        tool_choice: llm.ToolChoice,
        credentials: YandexCredentials,
        opts: _LLMOptions,
        sdk_getter,
    ) -> None:
        super().__init__(llm=llm, chat_ctx=chat_ctx, tools=tools)
        self._credentials = credentials
        self._opts = opts
        self._sdk_getter = sdk_getter
        self._tool_choice = tool_choice

    async def _run(self) -> None:
        """Stream tokens from YandexGPT."""
        sdk = self._sdk_getter()
        
        # Convert messages
        messages = _convert_messages(self._chat_ctx)
        
        # Convert tools if provided
        yandex_tools = _convert_tools(self._tools)
        
        try:
            # Get model and configure
            model = sdk.models.completions(self._opts.model)
            model = model.configure(
                temperature=self._opts.temperature,
                max_tokens=self._opts.max_tokens,
            )
            
            # Run completion (SDK handles streaming internally)
            # Note: yandex_cloud_ml_sdk run() returns iterator of alternatives
            result = model.run(messages)
            
            # Process result
            request_id = ""
            full_text = ""
            
            for alternative in result:
                # Each alternative contains the generated text
                if hasattr(alternative, 'text'):
                    text = alternative.text
                elif hasattr(alternative, 'message') and hasattr(alternative.message, 'text'):
                    text = alternative.message.text
                else:
                    text = str(alternative)
                
                # Emit the text as a chunk
                if text:
                    full_text = text
                    chunk = llm.ChatChunk(
                        request_id=request_id,
                        choices=[
                            llm.Choice(
                                delta=llm.ChoiceDelta(
                                    role="assistant",
                                    content=text,
                                ),
                                index=0,
                            )
                        ],
                    )
                    self._event_ch.send_nowait(chunk)
            
            # Check for tool calls in response
            # YandexGPT returns tool calls in toolCallList field
            if hasattr(result, 'tool_calls') and result.tool_calls:
                for tool_call in result.tool_calls:
                    func_call = llm.FunctionCallInfo(
                        tool_call_id=tool_call.get('id', ''),
                        function_info=llm.FunctionInfo(
                            name=tool_call.get('function', {}).get('name', ''),
                            arguments=json.dumps(
                                tool_call.get('function', {}).get('arguments', {})
                            ),
                        ),
                    )
                    chunk = llm.ChatChunk(
                        request_id=request_id,
                        choices=[
                            llm.Choice(
                                delta=llm.ChoiceDelta(
                                    role="assistant",
                                    tool_calls=[func_call],
                                ),
                                index=0,
                            )
                        ],
                    )
                    self._event_ch.send_nowait(chunk)
                    
        except Exception as e:
            logger.error(f"YandexGPT error: {e}")
            raise
