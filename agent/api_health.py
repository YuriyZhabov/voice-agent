"""API health check module for Voice Agent MVP.

Validates connectivity to all external APIs:
- LiveKit (WebRTC infrastructure)
- Deepgram (STT)
- OpenAI/CometAPI (LLM)
- ElevenLabs (TTS)

Requirements: 5.1, 5.2, 5.3
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from agent.config import AgentConfig


@dataclass
class HealthCheckResult:
    """Result of a single API health check."""
    service: str
    healthy: bool
    message: str
    latency_ms: float | None = None


@dataclass
class AllHealthChecks:
    """Results of all API health checks."""
    results: list[HealthCheckResult]
    
    @property
    def all_healthy(self) -> bool:
        """Return True if all services are healthy."""
        return all(r.healthy for r in self.results)
    
    def __str__(self) -> str:
        lines = ["API Health Check Results:"]
        for r in self.results:
            status = "✓" if r.healthy else "✗"
            latency = f" ({r.latency_ms:.0f}ms)" if r.latency_ms else ""
            lines.append(f"  {status} {r.service}: {r.message}{latency}")
        return "\n".join(lines)


async def check_livekit(config: AgentConfig) -> HealthCheckResult:
    """Check LiveKit API connectivity."""
    try:
        # LiveKit uses livekit-api package for REST API
        # For health check, we verify the URL is reachable via HTTP
        http_url = config.livekit_url.replace("wss://", "https://").replace("ws://", "http://")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            # LiveKit Cloud returns 404 on root, but that means it's reachable
            response = await client.get(http_url)
            latency = (time.perf_counter() - start) * 1000
            
            # Any response means the server is reachable
            return HealthCheckResult(
                service="LiveKit",
                healthy=True,
                message=f"Server reachable (HTTP {response.status_code})",
                latency_ms=latency,
            )
    except httpx.TimeoutException:
        return HealthCheckResult(
            service="LiveKit",
            healthy=False,
            message="Connection timeout",
        )
    except Exception as e:
        return HealthCheckResult(
            service="LiveKit",
            healthy=False,
            message=f"Error: {str(e)}",
        )


async def check_deepgram(config: AgentConfig) -> HealthCheckResult:
    """Check Deepgram API connectivity."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            response = await client.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {config.deepgram_api_key}"},
            )
            latency = (time.perf_counter() - start) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    service="Deepgram",
                    healthy=True,
                    message="API key valid",
                    latency_ms=latency,
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    service="Deepgram",
                    healthy=False,
                    message="Invalid API key",
                )
            else:
                return HealthCheckResult(
                    service="Deepgram",
                    healthy=False,
                    message=f"Unexpected status: {response.status_code}",
                )
    except httpx.TimeoutException:
        return HealthCheckResult(
            service="Deepgram",
            healthy=False,
            message="Connection timeout",
        )
    except Exception as e:
        return HealthCheckResult(
            service="Deepgram",
            healthy=False,
            message=f"Error: {str(e)}",
        )


async def check_openai(config: AgentConfig) -> HealthCheckResult:
    """Check OpenAI-compatible API connectivity."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            response = await client.get(
                f"{config.openai_base_url}/models",
                headers={"Authorization": f"Bearer {config.openai_api_key}"},
            )
            latency = (time.perf_counter() - start) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    service="OpenAI/CometAPI",
                    healthy=True,
                    message="API key valid",
                    latency_ms=latency,
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    service="OpenAI/CometAPI",
                    healthy=False,
                    message="Invalid API key",
                )
            else:
                return HealthCheckResult(
                    service="OpenAI/CometAPI",
                    healthy=False,
                    message=f"Unexpected status: {response.status_code}",
                )
    except httpx.TimeoutException:
        return HealthCheckResult(
            service="OpenAI/CometAPI",
            healthy=False,
            message="Connection timeout",
        )
    except Exception as e:
        return HealthCheckResult(
            service="OpenAI/CometAPI",
            healthy=False,
            message=f"Error: {str(e)}",
        )


async def check_elevenlabs(config: AgentConfig) -> HealthCheckResult:
    """Check ElevenLabs API connectivity."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            response = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": config.eleven_api_key},
            )
            latency = (time.perf_counter() - start) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    service="ElevenLabs",
                    healthy=True,
                    message="API key valid",
                    latency_ms=latency,
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    service="ElevenLabs",
                    healthy=False,
                    message="Invalid API key",
                )
            else:
                return HealthCheckResult(
                    service="ElevenLabs",
                    healthy=False,
                    message=f"Unexpected status: {response.status_code}",
                )
    except httpx.TimeoutException:
        return HealthCheckResult(
            service="ElevenLabs",
            healthy=False,
            message="Connection timeout",
        )
    except Exception as e:
        return HealthCheckResult(
            service="ElevenLabs",
            healthy=False,
            message=f"Error: {str(e)}",
        )


async def check_exolve(config: AgentConfig) -> HealthCheckResult:
    """Check MTS Exolve API connectivity."""
    if not config.exolve_api_key:
        return HealthCheckResult(
            service="MTS Exolve",
            healthy=True,
            message="Skipped (no API key configured)",
        )
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            response = await client.post(
                "https://api.exolve.ru/number/customer/v1/GetSIPList",
                headers={"Authorization": f"Bearer {config.exolve_api_key}"},
                json={},
            )
            latency = (time.perf_counter() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                sip_count = len(data.get("sip_list", []))
                return HealthCheckResult(
                    service="MTS Exolve",
                    healthy=True,
                    message=f"API key valid ({sip_count} SIP resources)",
                    latency_ms=latency,
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    service="MTS Exolve",
                    healthy=False,
                    message="Invalid API key",
                )
            else:
                return HealthCheckResult(
                    service="MTS Exolve",
                    healthy=False,
                    message=f"Unexpected status: {response.status_code}",
                )
    except httpx.TimeoutException:
        return HealthCheckResult(
            service="MTS Exolve",
            healthy=False,
            message="Connection timeout",
        )
    except Exception as e:
        return HealthCheckResult(
            service="MTS Exolve",
            healthy=False,
            message=f"Error: {str(e)}",
        )


async def check_all_apis(config: AgentConfig | None = None) -> AllHealthChecks:
    """Run health checks for all APIs concurrently.
    
    Args:
        config: AgentConfig instance. If None, loads from environment.
        
    Returns:
        AllHealthChecks with results for each service.
    """
    if config is None:
        from agent.config import load_config
        config = load_config()
    
    results = await asyncio.gather(
        check_livekit(config),
        check_deepgram(config),
        check_openai(config),
        check_elevenlabs(config),
        check_exolve(config),
    )
    
    return AllHealthChecks(results=list(results))


def run_health_checks() -> AllHealthChecks:
    """Synchronous wrapper for check_all_apis."""
    return asyncio.run(check_all_apis())


if __name__ == "__main__":
    # Run health checks when executed directly
    results = run_health_checks()
    print(results)
    exit(0 if results.all_healthy else 1)
