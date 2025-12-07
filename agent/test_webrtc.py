"""Test agent via WebRTC (LiveKit Playground).

Creates a room and dispatches the agent, then prints connection info
for testing via LiveKit Playground or any WebRTC client.

Usage:
    python -m agent.test_webrtc
"""

import asyncio
import os

from dotenv import load_dotenv
from livekit import api

from agent.config import load_config

load_dotenv()


async def create_test_room():
    """Create a test room and dispatch the agent."""
    config = load_config()
    
    room_name = "test-agent-room"
    
    print(f"Creating test room for WebRTC testing:")
    print(f"  Room: {room_name}")
    print(f"  Agent: {config.agent_name}")
    print()
    
    lk_api = api.LiveKitAPI()
    
    try:
        # Create room
        await lk_api.room.create_room(
            api.CreateRoomRequest(name=room_name)
        )
        print(f"Created room: {room_name}")
        
        # Dispatch agent
        await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=config.agent_name,
                room=room_name,
            )
        )
        print(f"Agent dispatched: {config.agent_name}")
        
        # Generate access token for user
        token = api.AccessToken(
            os.getenv("LIVEKIT_API_KEY"),
            os.getenv("LIVEKIT_API_SECRET"),
        )
        token.with_identity("test-user")
        token.with_name("Test User")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
        
        jwt = token.to_jwt()
        
        print()
        print("=" * 60)
        print("Connect to the room using LiveKit Playground or SDK:")
        print("=" * 60)
        print()
        print(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
        print(f"Room: {room_name}")
        print()
        print("Access Token (copy this):")
        print(jwt)
        print()
        print("=" * 60)
        print()
        print("Option 1: LiveKit Meet")
        print(f"  https://meet.livekit.io/?tab=custom#liveKitUrl={os.getenv('LIVEKIT_URL')}&token={jwt}")
        print()
        print("Option 2: LiveKit Playground")
        print("  1. Go to https://cloud.livekit.io")
        print("  2. Select your project")
        print("  3. Go to Playground")
        print("  4. Use the token above")
        print()
        print("Press Ctrl+C to exit and delete the room.")
        
        # Wait for user to cancel
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nCleaning up...")
        try:
            await lk_api.room.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )
            print(f"Deleted room: {room_name}")
        except Exception:
            pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await lk_api.aclose()


def main():
    print("Make sure the agent is running first:")
    print("  python -m agent.main dev")
    print()
    asyncio.run(create_test_room())


if __name__ == "__main__":
    main()
