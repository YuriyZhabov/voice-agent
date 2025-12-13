"""Global context for current call.

Provides a simple way to access call_id from anywhere in the agent code.
"""

import contextvars
from typing import Optional

# Context variable for current call_id
_current_call_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'current_call_id', default=None
)


def set_call_id(call_id: str) -> None:
    """Set the current call ID."""
    _current_call_id.set(call_id)


def get_call_id() -> Optional[str]:
    """Get the current call ID."""
    return _current_call_id.get()


def clear_call_id() -> None:
    """Clear the current call ID."""
    _current_call_id.set(None)
