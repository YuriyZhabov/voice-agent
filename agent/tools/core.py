"""Core agent tools.

Contains essential tools like end_call for managing the conversation flow.

Requirements: 4.1, 4.2, 4.3
"""

import asyncio
import logging

from livekit import api
from livekit.agents import RunContext, function_tool, get_job_context

logger = logging.getLogger(__name__)


@function_tool
async def end_call(context: RunContext, reason: str = "user_farewell") -> str:
    """End the call gracefully.
    
    Call this function when:
    - The user says goodbye (до свидания, пока, всего хорошего, etc.)
    - The user indicates they want to end the conversation
    - The conversation has naturally concluded
    
    Args:
        reason: Reason for ending the call (e.g., "user_farewell", "task_complete")
    
    Returns:
        Confirmation that the call will be ended.
    """
    # Check if call is already ending via userdata
    userdata = context.userdata
    if userdata.get("call_ending", False):
        return "Звонок уже завершается."
    
    # Mark call as ending
    userdata["call_ending"] = True
    
    logger.info(f"Initiating call end: reason={reason}")
    
    # Schedule hangup after a short delay to allow farewell message
    async def delayed_hangup():
        await asyncio.sleep(3.0)
        ctx = get_job_context()
        if ctx is not None:
            await ctx.api.room.delete_room(
                api.DeleteRoomRequest(room=ctx.room.name)
            )
    
    asyncio.create_task(delayed_hangup())
    
    return "Звонок будет завершён после прощания."


# Export list of tools from this module
TOOLS = [end_call]
