"""Supabase client for logging calls, transcripts, and tool executions."""

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
    """Log call start to Supabase."""
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
    status: str = "completed"
) -> bool:
    """Log call end to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "status": status,
            "end_time": datetime.utcnow().isoformat()
        }
        
        client.table("calls").update(data).eq("call_id", call_id).execute()
        logger.info(f"Logged call end: {call_id} ({status})")
        return True
    except Exception as e:
        logger.error(f"Failed to log call end: {e}")
        return False


async def log_transcript(
    call_id: str,
    role: str,
    content: str
) -> bool:
    """Log transcript message to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "call_id": call_id,
            "role": role,  # 'user', 'assistant', 'system'
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client.table("transcripts").insert(data).execute()
        logger.debug(f"Logged transcript: {call_id} [{role}]")
        return True
    except Exception as e:
        logger.error(f"Failed to log transcript: {e}")
        return False


async def log_tool_execution(
    call_id: str,
    tool_name: str,
    parameters: dict = None,
    result: Any = None,
    success: bool = True,
    latency_ms: int = None
) -> bool:
    """Log tool execution to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Convert result to dict if it's not already
        if result is not None and not isinstance(result, dict):
            result = {"value": str(result)}
        
        data = {
            "call_id": call_id,
            "tool_name": tool_name,
            "parameters": parameters or {},
            "result": result or {},
            "success": success,
            "latency_ms": latency_ms,
            "executed_at": datetime.utcnow().isoformat()
        }
        
        client.table("tool_executions").insert(data).execute()
        logger.debug(f"Logged tool execution: {tool_name} ({latency_ms}ms)")
        return True
    except Exception as e:
        logger.error(f"Failed to log tool execution: {e}")
        return False


async def log_alert(
    severity: str,
    service: str,
    message: str
) -> bool:
    """Log alert to Supabase."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        data = {
            "severity": severity,  # 'critical', 'warning', 'info'
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
