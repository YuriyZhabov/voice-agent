"""Pydantic models for tool calls and results.

Provides validated models for YandexGPT function calling format.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FunctionCall(BaseModel):
    """A function call from the LLM.
    
    Attributes:
        name: Function name to call
        arguments: Arguments to pass to the function
    """
    
    name: str = Field(..., description="Function name")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Function arguments")


class ToolCall(BaseModel):
    """A tool call wrapper in YandexGPT format.
    
    Attributes:
        functionCall: The function call details
    """
    
    functionCall: FunctionCall = Field(..., alias="functionCall")
    
    model_config = {"populate_by_name": True}


class FunctionResult(BaseModel):
    """Result of a function execution.
    
    Attributes:
        name: Function name that was called
        content: Result content as string
    """
    
    name: str = Field(..., description="Function name")
    content: str = Field(..., description="Result content")


class ToolResult(BaseModel):
    """A tool result wrapper in YandexGPT format.
    
    Attributes:
        functionResult: The function result details
    """
    
    functionResult: FunctionResult = Field(..., alias="functionResult")
    
    model_config = {"populate_by_name": True}


class ToolCallList(BaseModel):
    """List of tool calls from YandexGPT.
    
    Attributes:
        toolCalls: List of tool calls
    """
    
    toolCalls: list[ToolCall] = Field(default_factory=list, alias="toolCalls")
    
    model_config = {"populate_by_name": True}


class ToolResultList(BaseModel):
    """List of tool results for YandexGPT.
    
    Attributes:
        toolResults: List of tool results
    """
    
    toolResults: list[ToolResult] = Field(default_factory=list, alias="toolResults")
    
    model_config = {"populate_by_name": True}
    
    @classmethod
    def from_execution_results(cls, results: list[dict]) -> "ToolResultList":
        """Create from executor results.
        
        Args:
            results: List of dicts with functionResult key
            
        Returns:
            ToolResultList instance
        """
        tool_results = []
        for r in results:
            fr = r.get("functionResult", {})
            tool_results.append(ToolResult(
                functionResult=FunctionResult(
                    name=fr.get("name", ""),
                    content=fr.get("content", ""),
                )
            ))
        return cls(toolResults=tool_results)
