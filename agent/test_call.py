"""Test outbound call script.

Makes an outbound call to test the voice agent.
The agent will be dispatched to the room and handle the call.

Usage:
    python -m agent.test_call +79001234567
"""

import asyncio
import sys
import uuid

from dotenv import load_dotenv
from livekit import api

from agent.config import load_config

load_dotenv()


async def make_test_call(phone_number: str):
    """Make a test outbound call.
    
    Args:
        phone_number: Phone number to call in E.164 format (+7XXXXXXXXXX)
    """
    config = load_config()
    
    # Get outbound trunk ID from env or use default
    import os
    outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    
    if not outbound_trunk_id:
        print("Error: SIP_OUTBOUND_TRUNK_ID not set in .env")
        print("Create outbound trunk first:")
        print('  python -m agent.sip_setup --create-outbound --name "MTS Exolve Outbound" --address "sip.exolve.ru" --number "+79587401087" --username "USERNAME" --password "PASSWORD"')
        return
    
    # Generate unique room name
    room_name = f"call-{uuid.uuid4().hex[:8]}"
    
    print(f"Making test call:")
    print(f"  To: {phone_number}")
    print(f"  Room: {room_name}")
    print(f"  Trunk: {outbound_trunk_id}")
    print(f"  Agent: {config.agent_name}")
    print()
    
    lk_api = api.LiveKitAPI()
    
    try:
        # Create room first
        await lk_api.room.create_room(
            api.CreateRoomRequest(name=room_name)
        )
        print(f"Created room: {room_name}")
        
        # Dispatch agent to the room
        await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=config.agent_name,
                room=room_name,
            )
        )
        print(f"Agent dispatched: {config.agent_name}")
        
        # Wait a moment for agent to connect
        await asyncio.sleep(2)
        
        # Make the call with wait_until_answered
        print("Calling... (waiting for answer)")
        participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity="phone-user",
                wait_until_answered=True,  # Wait for call to be answered
            )
        )
        print(f"Call answered! Participant: {participant.participant_identity}")
        print()
        print("The agent should now connect to the room and greet the caller.")
        print("Press Ctrl+C to exit (call will continue).")
        
        # Wait for user to cancel
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await lk_api.aclose()


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m agent.test_call +79001234567")
        print()
        print("Make sure the agent is running first:")
        print("  python -m agent.main dev")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    
    if not phone_number.startswith("+"):
        print("Error: Phone number must be in E.164 format (+7XXXXXXXXXX)")
        sys.exit(1)
    
    asyncio.run(make_test_call(phone_number))


if __name__ == "__main__":
    main()
