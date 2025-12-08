"""Custom LLM wrapper for CometAPI (OpenAI-compatible).

This module provides a LangChain-compatible LLM wrapper for CometAPI,
which uses OpenAI-compatible API endpoints.
"""

import json
from typing import Any

import httpx
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from pydantic import Field


class CometapiLLM(LLM):
    """Custom LLM wrapper for CometAPI (OpenAI-compatible API).
    
    CometAPI provides OpenAI-compatible endpoints, so this wrapper
    uses the standard chat completions API format.
    
    Example:
        >>> llm = CometapiLLM(
        ...     api_key="your-api-key",
        ...     model="gpt-4o-mini"
        ... )
        >>> response = llm.invoke("Hello, how are you?")
    """
    
    api_key: str = Field(..., description="CometAPI API key")
    api_url: str = Field(
        default="https://api.cometapi.com/v1",
        description="CometAPI base URL"
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="Model name to use"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=2048,
        ge=1,
        description="Maximum tokens to generate"
    )
    timeout: float = Field(
        default=60.0,
        description="Request timeout in seconds"
    )

    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM type."""
        return "cometapi"
    
    @property
    def _identifying_params(self) -> dict[str, Any]:
        """Return identifying parameters for caching."""
        return {
            "model": self.model,
            "api_url": self.api_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def _call(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Send prompt to CometAPI and get response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if stop:
            payload["stop"] = stop
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def _acall(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Async version of _call."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if stop:
            payload["stop"] = stop
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def astream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        **kwargs: Any,
    ):
        """Stream response from CometAPI."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True,
        }
        
        if stop:
            payload["stop"] = stop
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.api_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
