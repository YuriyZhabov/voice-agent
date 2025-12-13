"""Core agent tools.

Contains essential tools like end_call for managing the conversation flow.

Requirements: 4.1, 4.2, 4.3
"""

import asyncio
import logging

from livekit import api
from livekit.agents import RunContext, function_tool, get_job_context

logger = logging.getLogger(__name__)


async def _hangup_call():
    """Hangup the call by deleting the room."""
    ctx = get_job_context()
    if ctx is None:
        logger.warning("hangup_call: no job context")
        return
    
    logger.info(f"Deleting room: {ctx.room.name}")
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(room=ctx.room.name)
    )


@function_tool
async def end_call(context: RunContext, reason: str = "user_farewell") -> str:
    """End the call gracefully.
    
    Call this function when the user wants to end the call.
    
    Args:
        reason: Reason for ending the call (e.g., "user_farewell", "task_complete")
    
    Returns:
        Farewell message to speak before hanging up.
    """
    logger.info(f"end_call tool invoked: reason={reason}")
    
    # Check if call is already ending via userdata
    try:
        userdata = context.userdata
        if userdata and userdata.get("call_ending", False):
            logger.info("end_call: call already ending")
            return "Звонок уже завершается."
        
        # Mark call as ending
        if userdata:
            userdata["call_ending"] = True
    except Exception as e:
        logger.warning(f"end_call: userdata not available: {e}")
    
    # Schedule hangup AFTER TTS finishes speaking
    # We use a fixed delay because we don't have access to LiveKit's RunContext
    # (our tools are called from custom YandexGPT LLM, not LiveKit Agent framework)
    async def hangup_after_delay():
        try:
            # Wait for TTS to finish speaking "До свидания! Всего хорошего!"
            # This phrase takes ~2 seconds to speak
            delay = 2.5
            logger.info(f"Waiting {delay}s for TTS to finish...")
            await asyncio.sleep(delay)
            logger.info("Delay finished, hanging up now")
            
            # Now hangup
            await _hangup_call()
        except Exception as e:
            logger.error(f"Error during hangup: {e}", exc_info=True)
    
    asyncio.create_task(hangup_after_delay())
    
    # Return farewell message that will be spoken by TTS
    return "До свидания! Всего хорошего!"


# Export list of tools from this module
TOOLS = [end_call]
