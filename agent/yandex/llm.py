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
        tools: list[llm.FunctionTool | llm.RawFunctionTool] | None = None,
        conn_options: APIConnectOptions = APIConnectOptions(),
        parallel_tool_calls: Any = None,
        tool_choice: Any = None,
        extra_kwargs: Any = None,
    ) -> "YandexLLMStream":
        """Generate chat completion.
        
        Args:
            chat_ctx: Chat context with message history
            tools: Optional list of function tools
            conn_options: Connection options
            parallel_tool_calls: Ignored for Yandex
            tool_choice: Ignored for Yandex
            extra_kwargs: Ignored for Yandex
        
        Returns:
            YandexLLMStream for streaming response
        """
        return YandexLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            credentials=self._credentials,
            opts=self._opts,
            sdk_getter=self._get_sdk,
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


class YandexLLMStream(llm.LLMStream):
    """Streaming LLM response from YandexGPT."""
    
    def __init__(
        self,
        *,
        llm: YandexLLM,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool | llm.RawFunctionTool],
        conn_options: APIConnectOptions,
        credentials: YandexCredentials,
        opts: _LLMOptions,
        sdk_getter,
    ) -> None:
        super().__init__(llm=llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._credentials = credentials
        self._opts = opts
        self._sdk_getter = sdk_getter

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
            # Get model and configure
            model = sdk.models.completions(self._opts.model)
            model = model.configure(temperature=self._opts.temperature)
            
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Run completion - SDK is sync, run in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: model.run(messages))
            
            logger.info(f"YandexGPT result: {result}")
            
            # Process result - GPTModelResult has alternatives tuple
            for alternative in result.alternatives:
                text = alternative.text
                logger.info(f"YandexGPT response: {text[:100] if text else 'empty'}...")
                
                if text:
                    # Emit chunk
                    chunk = ChatChunk(
                        id=request_id,
                        delta=ChoiceDelta(
                            role="assistant",
                            content=text,
                            tool_calls=[],
                        ),
                        usage=None,
                    )
                    self._event_ch.send_nowait(chunk)
                    
        except Exception as e:
            logger.error(f"YandexGPT error: {e}", exc_info=True)
            raise
