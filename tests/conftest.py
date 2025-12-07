"""Pytest configuration and fixtures for Voice Agent MVP tests."""

import pytest
from hypothesis import settings

# Configure Hypothesis for 100 iterations minimum
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=20)
settings.load_profile("ci")


@pytest.fixture
def sample_call_id() -> str:
    """Provide a sample call ID for testing."""
    return "test-call-123"


@pytest.fixture
def sample_system_prompt() -> str:
    """Provide a sample system prompt for testing."""
    return "Ты полезный голосовой ассистент. Отвечай кратко и по делу."
