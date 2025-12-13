"""Supabase client for comprehensive call logging and monitoring."""

import os
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import to avoid startup errors if supabase not installed
_supabase_client = None


def get_supabase_client():
    """Get or create Supabase client (singleton)."""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        logger.warning("Supabase not configured (SUPABASE_URL or SUPABASE_SERVICE_KEY missing)")
        return None
    
    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        logger.info(f"Supabase client initialized: {url}")
        return _supabase_client
    except ImportError:
        logger.warning("supabase-py not installed, run: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


async def log_call_start(
    call_id: str,
    phone_number: str,
    room_name: str,
    direction: str = "inbound",
    agent_version: str = None,
    metadata: dict = None
) -> bool:
    """Log call start to Supabase with full metadata."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "call_id": call_id,
            "phone_number": phone_number,
            "room_name": room_name,
            "direction": direction,
            "status": "active",
            "start_time": datetime.utcnow().isoformat(),
            "agent_version": agent_version or os.getenv("AGENT_NAME", "voice-agent"),
            "metadata": metadata or {}
        }
        
        client.table("calls").insert(data).execute()
        logger.info(f"Logged call start: {call_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to log call start: {e}")
        return False


async def log_call_end(
    call_id: str,
    status: str = "completed",
    end_reason: str = None,
    metrics: dict = None
) -> bool:
    """Log call end with metrics to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "status": status,
            "end_time": datetime.utcnow().isoformat()
        }
        
        # Add metrics to metadata if provided
        if metrics or end_reason:
            # Get current metadata first
            result = client.table("calls").select("metadata").eq("call_id", call_id).execute()
            current_metadata = result.data[0].get("metadata", {}) if result.data else {}
            
            if end_reason:
                current_metadata["end_reason"] = end_reason
            if metrics:
                current_metadata["metrics"] = metrics
            
            data["metadata"] = current_metadata
        
        client.table("calls").update(data).eq("call_id", call_id).execute()
        logger.info(f"Logged call end: {call_id} ({status})")
        return True
    except Exception as e:
        logger.error(f"Failed to log call end: {e}")
        return False


async def log_transcript(
    call_id: str,
    role: str,
    content: str,
    is_final: bool = True,
    language: str = "ru-RU",
    confidence: float = None
) -> bool:
    """Log transcript message to Supabase with metadata."""
    client = get_supabase_client()
    if not client:
        return False
    
    # Skip non-final transcripts to reduce noise
    if not is_final:
        return True
    
    # Clean up content - extract actual text from transcript object string
    clean_content = content
    if "transcript='" in content:
        try:
            start = content.find("transcript='") + len("transcript='")
            end = content.find("'", start)
            clean_content = content[start:end]
        except Exception:
            pass
    
    try:
        data = {
            "call_id": call_id,
            "role": role,
            "content": clean_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client.table("transcripts").insert(data).execute()
        logger.info(f"Logged transcript: {call_id} [{role}]: {clean_content[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to log transcript: {e}")
        return False


async def log_assistant_response(call_id: str, content: str) -> bool:
    """Log assistant response to Supabase."""
    return await log_transcript(call_id, "assistant", content, is_final=True)


async def log_tool_execution(
    call_id: str,
    tool_name: str,
    parameters: dict = None,
    result: Any = None,
    success: bool = True,
    latency_ms: int = None,
    error_message: str = None
) -> bool:
    """Log tool execution to Supabase with full details."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Convert result to dict if it's not already
        result_data = {}
        if result is not None:
            if isinstance(result, dict):
                result_data = result
            else:
                result_data = {"value": str(result)[:1000]}
        
        if error_message:
            result_data["error"] = error_message
        
        data = {
            "call_id": call_id,
            "tool_name": tool_name,
            "parameters": parameters or {},
            "result": result_data,
            "success": success,
            "latency_ms": latency_ms,
            "executed_at": datetime.utcnow().isoformat()
        }
        
        client.table("tool_executions").insert(data).execute()
        logger.info(f"Logged tool execution: {tool_name} (success={success}, {latency_ms}ms)")
        return True
    except Exception as e:
        logger.error(f"Failed to log tool execution: {e}")
        return False


async def log_alert(
    severity: str,
    service: str,
    message: str,
    call_id: str = None,
    metadata: dict = None
) -> bool:
    """Log alert to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "severity": severity,
            "service": service,
            "message": message,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
        client.table("alerts_history").insert(data).execute()
        logger.info(f"Logged alert: [{severity}] {service}: {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to log alert: {e}")
        return False


async def log_latency_metric(
    call_id: str,
    metric_type: str,
    value_ms: float,
    metadata: dict = None
) -> bool:
    """Log latency metric to Supabase metrics table."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "call_id": call_id,
            "metric_type": metric_type,
            "value_ms": round(value_ms, 2),
            "metadata": metadata or {},
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        client.table("call_metrics").insert(data).execute()
        logger.debug(f"Logged metric: {metric_type}={value_ms}ms")
        return True
    except Exception as e:
        logger.error(f"Failed to log metric: {e}")
        return False


async def log_llm_usage(
    call_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "yandexgpt",
    latency_ms: float = None
) -> bool:
    """Log LLM usage to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "call_id": call_id,
            "metric_type": "llm_usage",
            "value_ms": latency_ms or 0,
            "metadata": {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            },
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        client.table("call_metrics").insert(data).execute()
        logger.debug(f"Logged LLM usage: {prompt_tokens}+{completion_tokens} tokens")
        return True
    except Exception as e:
        logger.error(f"Failed to log LLM usage: {e}")
        return False


async def log_event(
    call_id: str,
    event_type: str,
    data: dict = None
) -> bool:
    """Log generic event to Supabase events table."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        event_data = {
            "call_id": call_id,
            "event_type": event_type,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client.table("call_events").insert(event_data).execute()
        logger.debug(f"Logged event: {event_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
        return False
