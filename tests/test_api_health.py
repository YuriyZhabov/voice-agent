"""Unit tests for API health check module."""

import pytest
from agent.api_health import HealthCheckResult, AllHealthChecks


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_healthy_result(self):
        """Healthy result has correct attributes."""
        result = HealthCheckResult(
            service="Test",
            healthy=True,
            message="OK",
            latency_ms=100.0,
        )
        assert result.healthy is True
        assert result.latency_ms == 100.0

    def test_unhealthy_result(self):
        """Unhealthy result has correct attributes."""
        result = HealthCheckResult(
            service="Test",
            healthy=False,
            message="Error",
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
            HealthCheckResult("B", False, "Error"),
        ])
        assert results.all_healthy is False

    def test_str_representation(self):
        """String representation includes all services."""
        results = AllHealthChecks(results=[
            HealthCheckResult("LiveKit", True, "OK", 50.0),
            HealthCheckResult("Yandex", False, "Error"),
        ])
        output = str(results)
        assert "LiveKit" in output
        assert "Yandex" in output
        assert "✓" in output
        assert "✗" in output
