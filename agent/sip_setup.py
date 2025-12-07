"""SIP setup script for LiveKit + MTS Exolve integration.

Provides utilities to create and manage SIP trunks and dispatch rules
for incoming phone calls via MTS Exolve.

Requirements: 1.1, 1.2
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv
from livekit import api

# Load environment variables from .env file
load_dotenv()


class SIPSetup:
    """Setup and manage SIP trunks for MTS Exolve integration.
    
    Uses LiveKit API to create inbound trunks and dispatch rules
    for routing incoming SIP calls to the voice agent.
    
    Environment variables required:
        LIVEKIT_URL: LiveKit server URL
        LIVEKIT_API_KEY: LiveKit API key
        LIVEKIT_API_SECRET: LiveKit API secret
    """
    
    def __init__(self):
        """Initialize SIPSetup with LiveKit API client."""
        # Uses LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET from env
        self.lk_api = api.LiveKitAPI()
    
    async def create_inbound_trunk(self, name: str, phone_numbers: list[str]) -> str:
        """Create an inbound SIP trunk for receiving calls.
        
        Args:
            name: Name for the trunk (e.g., "MTS Exolve Inbound")
            phone_numbers: List of phone numbers in E.164 format (+7XXXXXXXXXX)
            
        Returns:
            The created trunk's SIP trunk ID.
        """
        trunk = await self.lk_api.sip.create_sip_inbound_trunk(
            api.CreateSIPInboundTrunkRequest(
                trunk=api.SIPInboundTrunkInfo(
                    name=name,
                    numbers=phone_numbers,
                )
            )
        )
        print(f"Created inbound trunk: {trunk.sip_trunk_id}")
        return trunk.sip_trunk_id

    async def create_dispatch_rule(
        self,
        name: str = "Voice Agent Dispatch",
        room_prefix: str = "call-",
        agent_name: str = "voice-agent-mvp",
    ) -> str:
        """Create a dispatch rule with explicit agent dispatch.
        
        Args:
            name: Name for the dispatch rule
            room_prefix: Prefix for room names (e.g., "call-")
            agent_name: Agent name for dispatch (must match @server.rtc_session)
            
        Returns:
            The created dispatch rule's ID.
        """
        rule = await self.lk_api.sip.create_dispatch_rule(
            api.CreateSIPDispatchRuleRequest(
                name=name,
                rule=api.SIPDispatchRule(
                    dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                        room_prefix=room_prefix,
                    )
                ),
                room_config=api.RoomConfiguration(
                    agents=[api.RoomAgentDispatch(agent_name=agent_name)]
                ),
            )
        )
        print(f"Created dispatch rule: {rule.sip_dispatch_rule_id}")
        return rule.sip_dispatch_rule_id
    
    async def list_inbound_trunks(self) -> list:
        """List all inbound SIP trunks.
        
        Returns:
            List of SIPInboundTrunkInfo objects.
        """
        response = await self.lk_api.sip.list_inbound_trunk(
            api.ListSIPInboundTrunkRequest()
        )
        return list(response.items)
    
    async def list_dispatch_rules(self) -> list:
        """List all dispatch rules.
        
        Returns:
            List of SIPDispatchRuleInfo objects.
        """
        response = await self.lk_api.sip.list_dispatch_rule(
            api.ListSIPDispatchRuleRequest()
        )
        return list(response.items)
    
    async def delete_inbound_trunk(self, trunk_id: str) -> None:
        """Delete an inbound SIP trunk.
        
        Args:
            trunk_id: The SIP trunk ID to delete.
        """
        await self.lk_api.sip.delete_sip_trunk(
            api.DeleteSIPTrunkRequest(sip_trunk_id=trunk_id)
        )
        print(f"Deleted trunk: {trunk_id}")
    
    async def delete_dispatch_rule(self, rule_id: str) -> None:
        """Delete a dispatch rule.
        
        Args:
            rule_id: The dispatch rule ID to delete.
        """
        await self.lk_api.sip.delete_sip_dispatch_rule(
            api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=rule_id)
        )
        print(f"Deleted dispatch rule: {rule_id}")
    
    async def create_outbound_trunk(
        self,
        name: str,
        address: str,
        numbers: list[str],
        auth_username: str | None = None,
        auth_password: str | None = None,
    ) -> str:
        """Create an outbound SIP trunk for making calls.
        
        Args:
            name: Name for the trunk (e.g., "MTS Exolve Outbound")
            address: SIP server address (e.g., "sip.exolve.ru")
            numbers: List of caller ID numbers in E.164 format
            auth_username: SIP authentication username
            auth_password: SIP authentication password
            
        Returns:
            The created trunk's SIP trunk ID.
        """
        trunk = await self.lk_api.sip.create_outbound_trunk(
            api.CreateSIPOutboundTrunkRequest(
                trunk=api.SIPOutboundTrunkInfo(
                    name=name,
                    address=address,
                    numbers=numbers,
                    auth_username=auth_username or "",
                    auth_password=auth_password or "",
                )
            )
        )
        print(f"Created outbound trunk: {trunk.sip_trunk_id}")
        return trunk.sip_trunk_id
    
    async def list_outbound_trunks(self) -> list:
        """List all outbound SIP trunks.
        
        Returns:
            List of SIPOutboundTrunkInfo objects.
        """
        response = await self.lk_api.sip.list_outbound_trunk(
            api.ListSIPOutboundTrunkRequest()
        )
        return list(response.items)
    
    async def make_call(
        self,
        trunk_id: str,
        phone_number: str,
        room_name: str,
        participant_identity: str = "caller",
    ) -> str:
        """Make an outbound call via SIP.
        
        Creates a SIP participant in the specified room, which initiates
        an outbound call to the given phone number.
        
        Args:
            trunk_id: Outbound trunk ID to use
            phone_number: Phone number to call in E.164 format
            room_name: LiveKit room name to connect the call to
            participant_identity: Identity for the SIP participant
            
        Returns:
            The SIP participant ID.
        """
        participant = await self.lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=participant_identity,
            )
        )
        print(f"Call initiated to {phone_number} in room {room_name}")
        return participant.sip_participant_id
    
    async def close(self):
        """Close the API client."""
        await self.lk_api.aclose()


async def main():
    """CLI entry point for SIP setup."""
    parser = argparse.ArgumentParser(
        description="SIP Setup for Voice Agent MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agent.sip_setup --list
  python -m agent.sip_setup --create-trunk --name "MTS Exolve" --number "+79587401087"
  python -m agent.sip_setup --create-outbound --name "MTS Exolve Out" --address "sip.exolve.ru" --number "+79587401087"
  python -m agent.sip_setup --create-rule --agent-name "voice-agent-mvp"
  python -m agent.sip_setup --call --trunk-id ST_xxx --to "+79001234567" --room "test-call"
  python -m agent.sip_setup --delete-trunk ST_xxxxx
  python -m agent.sip_setup --delete-rule SDR_xxxxx
        """,
    )
    parser.add_argument("--list", action="store_true", help="List all trunks and rules")
    parser.add_argument("--create-trunk", action="store_true", help="Create inbound trunk")
    parser.add_argument("--create-outbound", action="store_true", help="Create outbound trunk")
    parser.add_argument("--create-rule", action="store_true", help="Create dispatch rule")
    parser.add_argument("--call", action="store_true", help="Make outbound call")
    parser.add_argument("--delete-trunk", type=str, metavar="ID", help="Delete trunk by ID")
    parser.add_argument("--delete-rule", type=str, metavar="ID", help="Delete rule by ID")
    parser.add_argument("--name", type=str, default="MTS Exolve", help="Trunk/rule name")
    parser.add_argument("--number", type=str, help="Phone number (+7XXXXXXXXXX)")
    parser.add_argument("--address", type=str, default="sip.exolve.ru", help="SIP server address")
    parser.add_argument("--username", type=str, help="SIP auth username")
    parser.add_argument("--password", type=str, help="SIP auth password")
    parser.add_argument("--trunk-id", type=str, help="Trunk ID for outbound call")
    parser.add_argument("--to", type=str, help="Phone number to call")
    parser.add_argument("--room", type=str, help="Room name for call")
    parser.add_argument("--agent-name", type=str, default="voice-agent-mvp", help="Agent name")
    parser.add_argument("--room-prefix", type=str, default="call-", help="Room prefix")
    args = parser.parse_args()
    
    setup = SIPSetup()
    
    try:
        if args.list:
            trunks = await setup.list_inbound_trunks()
            print(f"\nInbound Trunks ({len(trunks)}):")
            if trunks:
                for t in trunks:
                    print(f"  - {t.sip_trunk_id}: {t.name}")
                    if hasattr(t, 'numbers') and t.numbers:
                        print(f"    Numbers: {', '.join(t.numbers)}")
            else:
                print("  (none)")
            
            outbound = await setup.list_outbound_trunks()
            print(f"\nOutbound Trunks ({len(outbound)}):")
            if outbound:
                for t in outbound:
                    print(f"  - {t.sip_trunk_id}: {t.name}")
                    if hasattr(t, 'address'):
                        print(f"    Address: {t.address}")
                    if hasattr(t, 'numbers') and t.numbers:
                        print(f"    Numbers: {', '.join(t.numbers)}")
            else:
                print("  (none)")
            
            rules = await setup.list_dispatch_rules()
            print(f"\nDispatch Rules ({len(rules)}):")
            if rules:
                for r in rules:
                    print(f"  - {r.sip_dispatch_rule_id}: {r.name}")
            else:
                print("  (none)")
        
        if args.create_trunk:
            if not args.number:
                print("Error: --number required for --create-trunk")
                return
            await setup.create_inbound_trunk(args.name, [args.number])
        
        if args.create_outbound:
            if not args.number:
                print("Error: --number required for --create-outbound")
                return
            await setup.create_outbound_trunk(
                name=args.name,
                address=args.address,
                numbers=[args.number],
                auth_username=args.username,
                auth_password=args.password,
            )
        
        if args.create_rule:
            await setup.create_dispatch_rule(
                name=args.name + " Dispatch",
                room_prefix=args.room_prefix,
                agent_name=args.agent_name,
            )
        
        if args.call:
            if not args.trunk_id or not args.to or not args.room:
                print("Error: --trunk-id, --to, and --room required for --call")
                return
            await setup.make_call(
                trunk_id=args.trunk_id,
                phone_number=args.to,
                room_name=args.room,
            )
        
        if args.delete_trunk:
            await setup.delete_inbound_trunk(args.delete_trunk)
        
        if args.delete_rule:
            await setup.delete_dispatch_rule(args.delete_rule)
    
    finally:
        await setup.close()


if __name__ == "__main__":
    asyncio.run(main())
