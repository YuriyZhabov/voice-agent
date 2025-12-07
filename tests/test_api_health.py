"""Tests for API health check module.

Tests connectivity to external APIs using real credentials from .env.
These tests require network access and valid API keys.

Requirements: 5.1, 5.2, 5.3
"""

import pytest

from agent.api_health import (
    AllHealthChecks,
    HealthCheckResult,
    check_all_apis,
    check_deepgram,
    check_elevenlabs,
    check_exolve,
    check_livekit,
    check_openai,
)
from agent.config import load_config


@pytest.fixture
def config():
    """Load real config from .env file."""
    return load_config()


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_healthy_result(self):
        """Healthy result has correct attributes."""
        result = HealthCheckResult(
            service="Test",
            healthy=True,
            message="OK",
            latency_ms=100.5,
        )
        assert result.service == "Test"
        assert result.healthy is True
        assert result.message == "OK"
        assert result.latency_ms == 100.5

    def test_unhealthy_result(self):
        """Unhealthy result has correct attributes."""
        result = HealthCheckResult(
            service="Test",
            healthy=False,
            message="Connection failed",
        )
        assert result.healthy is False
        assert result.latency_ms is None


class TestAllHealthChecks:
    """Test AllHealthChecks dataclass."""

    def test_all_healthy_true(self):
        """all_healthy returns True when all services healthy."""
        results = AllHealthChecks(results=[
            HealthCheckResult("A", True, "OK"),
            HealthCheckResult("B", True, "OK"),
        ])
        assert results.all_healthy is True

    def test_all_healthy_false(self):
        """all_healthy returns False when any service unhealthy."""
        results = AllHealthChecks(results=[
            HealthCheckResult("A", True, "OK"),
            HealthCheckResult("B", False, "Failed"),
        ])
        assert results.all_healthy is False

    def test_str_representation(self):
        """String representation includes all services."""
        results = AllHealthChecks(results=[
            HealthCheckResult("ServiceA", True, "OK", 50.0),
            HealthCheckResult("ServiceB", False, "Failed"),
        ])
        output = str(results)
        assert "ServiceA" in output
        assert "ServiceB" in output
        assert "✓" in output
        assert "✗" in output


@pytest.mark.asyncio
class TestLiveKitHealthCheck:
    """Test LiveKit API connectivity."""

    async def test_livekit_reachable(self, config):
        """LiveKit server should be reachable with valid config."""
        result = await check_livekit(config)
        
        assert result.service == "LiveKit"
        assert result.healthy is True, f"LiveKit check failed: {result.message}"
        assert result.latency_ms is not None
        assert result.latency_ms > 0


@pytest.mark.asyncio
class TestDeepgramHealthCheck:
    """Test Deepgram API connectivity."""

    async def test_deepgram_api_key_valid(self, config):
        """Deepgram API key should be valid."""
        result = await check_deepgram(config)
        
        assert result.service == "Deepgram"
        assert result.healthy is True, f"Deepgram check failed: {result.message}"
        assert result.latency_ms is not None


@pytest.mark.asyncio
class TestOpenAIHealthCheck:
    """Test OpenAI/CometAPI connectivity."""

    async def test_openai_api_key_valid(self, config):
        """OpenAI-compatible API key should be valid."""
        result = await check_openai(config)
        
        assert result.service == "OpenAI/CometAPI"
        assert result.healthy is True, f"OpenAI check failed: {result.message}"
        assert result.latency_ms is not None


@pytest.mark.asyncio
class TestElevenLabsHealthCheck:
    """Test ElevenLabs API connectivity."""

    async def test_elevenlabs_api_key_valid(self, config):
        """ElevenLabs API key should be valid."""
        result = await check_elevenlabs(config)
        
        assert result.service == "ElevenLabs"
        assert result.healthy is True, f"ElevenLabs check failed: {result.message}"
        assert result.latency_ms is not None


@pytest.mark.asyncio
class TestExolveHealthCheck:
    """Test MTS Exolve API connectivity."""

    async def test_exolve_api_key_valid(self, config):
        """MTS Exolve API key should be valid (if configured)."""
        result = await check_exolve(config)
        
        assert result.service == "MTS Exolve"
        assert result.healthy is True, f"Exolve check failed: {result.message}"
        # latency_ms may be None if skipped (no API key)
        if config.exolve_api_key:
            assert result.latency_ms is not None


@pytest.mark.asyncio
class TestAllAPIsHealthCheck:
    """Test combined health check for all APIs."""

    async def test_all_apis_healthy(self, config):
        """All APIs should be healthy with valid config."""
        results = await check_all_apis(config)
        
        assert len(results.results) == 5  # LiveKit, Deepgram, OpenAI, ElevenLabs, Exolve
        
        # Print results for debugging
        print("\n" + str(results))
        
        # Check each service
        for result in results.results:
            assert result.healthy is True, f"{result.service} failed: {result.message}"
        
        assert results.all_healthy is True
