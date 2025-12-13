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
    
    # Get job context to access room
    ctx = get_job_context()
    if ctx is None:
        logger.warning("end_call: no job context available")
        return "Не удалось завершить звонок."
    
    room_name = ctx.room.name if ctx.room else "unknown"
    logger.info(f"Scheduling hangup for room: {room_name}")
    
    # Schedule hangup after delay to allow farewell message to be spoken
    async def delayed_hangup():
        await asyncio.sleep(5.0)  # Wait for TTS to finish farewell
        try:
            job_ctx = get_job_context()
            if job_ctx is not None and job_ctx.room:
                logger.info(f"Executing hangup for room: {job_ctx.room.name}")
                await job_ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=job_ctx.room.name)
                )
        except Exception as e:
            logger.error(f"Error during hangup: {e}")
    
    asyncio.create_task(delayed_hangup())
    
    return "Попрощайся с пользователем, звонок завершится через несколько секунд."


# Export list of tools from this module
TOOLS = [end_call]
