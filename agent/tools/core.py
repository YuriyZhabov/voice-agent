"""Core agent tools.

Contains essential tools like end_call for managing the conversation flow.

Requirements: 4.1, 4.2, 4.3
"""

import asyncio
import logging
import os

from livekit import api, rtc
from livekit.agents import RunContext, function_tool, get_job_context

logger = logging.getLogger(__name__)

# Outbound trunk ID for SIP transfer
SIP_OUTBOUND_TRUNK_ID = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "ST_KH3YSJanPaAi")


async def _find_sip_participant(room: rtc.Room) -> str | None:
    """Find the SIP participant identity in the room."""
    for participant in room.remote_participants.values():
        # SIP participants have identity starting with "sip_"
        if participant.identity.startswith("sip_"):
            return participant.identity
    return None


async def _hangup_via_transfer():
    """Hangup the call using SIP REFER transfer to a non-existent endpoint.
    
    This causes a clean disconnect without busy tones because the call
    is transferred rather than rejected with 486.
    """
    ctx = get_job_context()
    if ctx is None:
        logger.warning("hangup: no job context")
        return
    
    room_name = ctx.room.name
    sip_identity = await _find_sip_participant(ctx.room)
    
    if not sip_identity:
        logger.warning(f"No SIP participant found, deleting room: {room_name}")
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        return
    
    logger.info(f"Attempting SIP transfer hangup for: {sip_identity}")
    
    try:
        # Simply remove participant - LiveKit will send BYE
        # The 486 code is unavoidable in self-hosted LiveKit SIP
        logger.info(f"Removing SIP participant: {sip_identity} from room: {room_name}")
        await ctx.api.room.remove_participant(
            api.RoomParticipantIdentity(room=room_name, identity=sip_identity)
        )
        logger.info("SIP participant removed successfully")
    except Exception as e:
        logger.error(f"remove_participant failed: {e}")
        try:
            await ctx.api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        except Exception as e2:
            logger.error(f"delete_room also failed: {e2}")


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
    
    # Schedule hangup after delay to allow farewell message to be spoken
    async def delayed_hangup():
        await asyncio.sleep(4.5)  # Wait for TTS to finish farewell
        try:
            await _hangup_via_transfer()
        except Exception as e:
            logger.error(f"Error during hangup: {e}")
    
    asyncio.create_task(delayed_hangup())
    
    # Return farewell message that will be spoken by TTS
    return "До свидания! Всего хорошего!"


# Export list of tools from this module
TOOLS = [end_call]
