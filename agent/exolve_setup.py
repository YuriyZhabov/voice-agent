"""MTS Exolve setup script for SIP forwarding to LiveKit.

Configures call forwarding from Exolve number to LiveKit SIP endpoint.

Requirements: 1.1, 1.2
"""

import asyncio
import argparse

import httpx
from dotenv import load_dotenv

from agent.config import load_config

# Load environment variables
load_dotenv()


class ExolveSetup:
    """Setup and manage MTS Exolve SIP configuration."""
    
    def __init__(self, api_key: str):
        """Initialize ExolveSetup with API key."""
        self.api_key = api_key
        self.base_url = "https://api.exolve.ru"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    async def get_number_info(self, number: int) -> dict:
        """Get information about a phone number.
        
        Args:
            number: Phone number without + (e.g., 79587401087)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/v1/GetInfo",
                headers=self.headers,
                json={"number": number},
            )
            response.raise_for_status()
            return response.json()
    
    async def set_call_forwarding(
        self,
        number: int,
        sip_id: str,
    ) -> dict:
        """Set call forwarding to SIP ID.
        
        Uses SetCallForwarding API to forward incoming calls to a SIP resource.
        
        Args:
            number: Phone number without + (e.g., 79587401087)
            sip_id: SIP ID to forward to (e.g., 883140776944348)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/v1/SetCallForwarding",
                headers=self.headers,
                json={
                    "number": number,
                    "forwarding_to_sip_id": sip_id,
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def set_call_forwarding_to_sip_uri(
        self,
        number: int,
        sip_uri: str,
    ) -> dict:
        """Set call forwarding to external SIP URI.
        
        Uses call_forwarding_type: 1 (CALL_FORWARDING_TYPE_SIP)
        and call_forwarding_sip with sip_uri field.
        
        Format: sip_uri should be "user@domain" or "+phone@domain"
        
        Args:
            number: Phone number without + (e.g., 79587401087)
            sip_uri: External SIP URI (e.g., +79587401087@domain.sip.livekit.cloud)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/v1/SetCallForwarding",
                headers=self.headers,
                json={
                    "number_code": number,  # uint64 format per API docs
                    "call_forwarding_type": 1,  # 1 = external SIP
                    "call_forwarding_sip": {
                        "sip_uri": sip_uri,
                    },
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def get_call_forwarding(self, number: int) -> dict:
        """Get current call forwarding settings for a number.
        
        Args:
            number: Phone number without + (e.g., 79587401087)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/v1/GetCallForwarding",
                headers=self.headers,
                json={"number_code": number},
            )
            response.raise_for_status()
            return response.json()
    
    async def clear_call_forwarding(self, number: int) -> dict:
        """Clear call forwarding settings for a number.
        
        Args:
            number: Phone number without + (e.g., 79587401087)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/v1/SetCallForwarding",
                headers=self.headers,
                json={
                    "number_code": number,
                    "call_forwarding_type": 0,  # 0 = disabled
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_sip_list(self) -> list:
        """Get list of SIP resources."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/customer/v1/GetSIPList",
                headers=self.headers,
                json={},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("sip_list", [])
    
    async def get_sip_attributes(self, sip_resource_id: str) -> dict:
        """Get SIP resource attributes including password.
        
        Args:
            sip_resource_id: SIP resource ID
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/sip/v1/GetAttributes",
                headers=self.headers,
                json={"sip_resource_id": sip_resource_id},
            )
            response.raise_for_status()
            return response.json()
    
    async def set_sip_destination(
        self,
        sip_resource_id: str,
        destination: str,
    ) -> dict:
        """Set SIP destination for incoming calls.
        
        Args:
            sip_resource_id: SIP resource ID
            destination: SIP URI destination (e.g., sip:xxx.sip.livekit.cloud)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/sip/v1/SetDestination",
                headers=self.headers,
                json={
                    "sip_resource_id": sip_resource_id,
                    "destination": destination,
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def get_numbers_list(self) -> dict:
        """Get list of phone numbers in the account."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/number/customer/v1/GetList",
                headers=self.headers,
                json={},
            )
            response.raise_for_status()
            return response.json()


async def main():
    """CLI entry point for Exolve setup."""
    parser = argparse.ArgumentParser(
        description="MTS Exolve Setup for Voice Agent MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agent.exolve_setup --info
  python -m agent.exolve_setup --sip-list
  python -m agent.exolve_setup --sip-attributes
  python -m agent.exolve_setup --get-forwarding
  python -m agent.exolve_setup --set-forwarding
  python -m agent.exolve_setup --clear-forwarding
        """,
    )
    parser.add_argument("--info", action="store_true", help="Get number info")
    parser.add_argument("--numbers", action="store_true", help="List phone numbers")
    parser.add_argument("--sip-list", action="store_true", help="List SIP resources")
    parser.add_argument("--sip-attributes", action="store_true", help="Get SIP attributes")
    parser.add_argument("--set-destination", action="store_true", help="Set SIP destination to LiveKit (deprecated)")
    parser.add_argument("--get-forwarding", action="store_true", help="Get current call forwarding settings")
    parser.add_argument("--set-forwarding", action="store_true", help="Set call forwarding to LiveKit SIP")
    parser.add_argument("--clear-forwarding", action="store_true", help="Clear call forwarding")
    args = parser.parse_args()
    
    config = load_config()
    
    if not config.exolve_api_key:
        print("Error: EXOLVE_API_KEY not configured")
        return
    
    setup = ExolveSetup(config.exolve_api_key)
    
    if args.info:
        # Remove + from phone number
        number = int(config.exolve_phone_number.replace("+", ""))
        print(f"\nGetting info for number: {number}")
        try:
            info = await setup.get_number_info(number)
            print(f"Number info: {info}")
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
    
    if args.numbers:
        print("\nPhone Numbers in account:")
        try:
            numbers = await setup.get_numbers_list()
            print(f"  Response: {numbers}")
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
    
    if args.sip_list:
        print("\nSIP Resources:")
        sip_list = await setup.get_sip_list()
        for sip in sip_list:
            print(f"  - ID: {sip.get('sip_resource_id')}")
            print(f"    Name: {sip.get('sip_name')}")
            print(f"    Username: {sip.get('user_name')}")
            print(f"    Domain: {sip.get('domain')}")
            print(f"    CLI: {sip.get('cli')}")
            print()
    
    if args.sip_attributes:
        if not config.exolve_sip_resource_id:
            print("Error: EXOLVE_SIP_RESOURCE_ID not configured")
            return
        print(f"\nSIP Attributes for {config.exolve_sip_resource_id}:")
        try:
            attrs = await setup.get_sip_attributes(config.exolve_sip_resource_id)
            print(f"  Full response: {attrs}")
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
    
    if args.get_forwarding:
        if not config.exolve_phone_number:
            print("Error: EXOLVE_PHONE_NUMBER not configured")
            return
        number = int(config.exolve_phone_number.replace("+", ""))
        print(f"\nGetting call forwarding for {number}:")
        try:
            result = await setup.get_call_forwarding(number)
            print(f"  Result: {result}")
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
    
    if args.clear_forwarding:
        if not config.exolve_phone_number:
            print("Error: EXOLVE_PHONE_NUMBER not configured")
            return
        number = int(config.exolve_phone_number.replace("+", ""))
        print(f"\nClearing call forwarding for {number}:")
        try:
            result = await setup.clear_call_forwarding(number)
            print(f"Success! Result: {result}")
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
    
    if args.set_forwarding or args.set_destination:
        if not config.exolve_phone_number:
            print("Error: EXOLVE_PHONE_NUMBER not configured")
            return
        
        number = int(config.exolve_phone_number.replace("+", ""))
        
        # LiveKit SIP URI format: +phone@livekit-sip-domain
        # The phone number in the URI helps LiveKit route to the correct trunk
        livekit_domain = "5o0nn71q1ga.sip.livekit.cloud"
        sip_uri = f"+{number}@{livekit_domain}"
        
        print(f"\nSetting call forwarding via SetCallForwarding API:")
        print(f"  Number: {number}")
        print(f"  Destination SIP URI: {sip_uri}")
        
        try:
            result = await setup.set_call_forwarding_to_sip_uri(number, sip_uri)
            print(f"Success! Result: {result}")
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")


if __name__ == "__main__":
    asyncio.run(main())
