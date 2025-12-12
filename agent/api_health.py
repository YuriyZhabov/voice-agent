"""API health check module for Voice Agent.

Validates connectivity to external APIs:
- LiveKit (WebRTC infrastructure)
- Yandex Cloud (STT, TTS, LLM)
"""

import asyncio
from dataclasses import dataclass

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
        http_url = config.livekit_url.replace("wss://", "https://").replace("ws://", "http://")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            response = await client.get(http_url)
            latency = (time.perf_counter() - start) * 1000
            
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


async def check_yandex_cloud(config: AgentConfig) -> HealthCheckResult:
    """Check Yandex Cloud API connectivity."""
    if not config.yc_api_key and not config.yc_iam_token:
        return HealthCheckResult(
            service="Yandex Cloud",
            healthy=False,
            message="No API key or IAM token configured",
        )
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            import time
            start = time.perf_counter()
            
            headers = {}
            if config.yc_api_key:
                headers["Authorization"] = f"Api-Key {config.yc_api_key}"
            elif config.yc_iam_token:
                headers["Authorization"] = f"Bearer {config.yc_iam_token}"
            
            if config.yc_folder_id:
                headers["x-folder-id"] = config.yc_folder_id
            
            # Check LLM API endpoint
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "modelUri": f"gpt://{config.yc_folder_id}/yandexgpt-lite",
                    "completionOptions": {"maxTokens": 1},
                    "messages": [{"role": "user", "text": "test"}],
                },
            )
            latency = (time.perf_counter() - start) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    service="Yandex Cloud",
                    healthy=True,
                    message="API key valid, LLM accessible",
                    latency_ms=latency,
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    service="Yandex Cloud",
                    healthy=False,
                    message="Invalid API key or IAM token",
                )
            else:
                return HealthCheckResult(
                    service="Yandex Cloud",
                    healthy=False,
                    message=f"Unexpected status: {response.status_code}",
                )
    except httpx.TimeoutException:
        return HealthCheckResult(
            service="Yandex Cloud",
            healthy=False,
            message="Connection timeout",
        )
    except Exception as e:
        return HealthCheckResult(
            service="Yandex Cloud",
            healthy=False,
            message=f"Error: {str(e)}",
        )


async def check_all_apis(config: AgentConfig | None = None) -> AllHealthChecks:
    """Run health checks for all APIs concurrently."""
    if config is None:
        from agent.config import load_config
        config = load_config()
    
    results = await asyncio.gather(
        check_livekit(config),
        check_yandex_cloud(config),
    )
    
    return AllHealthChecks(results=list(results))


def run_health_checks() -> AllHealthChecks:
    """Synchronous wrapper for check_all_apis."""
    return asyncio.run(check_all_apis())


if __name__ == "__main__":
    results = run_health_checks()
    print(results)
    exit(0 if results.all_healthy else 1)
