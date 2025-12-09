"""Time-related agent tools.

Provides tools for getting current time in Moscow timezone.

Requirements: 3.1, 3.2, 3.3
"""

import logging
from datetime import datetime

from livekit.agents import RunContext, function_tool

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

logger = logging.getLogger(__name__)

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


@function_tool
async def get_current_time(context: RunContext, timezone: str = "Europe/Moscow") -> str:
    """Get current time in specified timezone.
    
    Call this function when the user asks what time it is.
    Returns the current time formatted in Russian.
    
    Args:
        timezone: Timezone name (default: Europe/Moscow)
    
    Returns:
        Current time in specified timezone in Russian format.
    """
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = MOSCOW_TZ
    now = datetime.now(tz)
    
    # Format time in Russian
    hours = now.hour
    minutes = now.minute
    
    # Russian time format
    time_str = f"{hours:02d}:{minutes:02d}"
    date_str = now.strftime("%d.%m.%Y")
    
    logger.info(f"get_current_time called: {time_str}")
    
    return f"Сейчас {time_str} по московскому времени, {date_str}."


# Export list of tools from this module
TOOLS = [get_current_time]
