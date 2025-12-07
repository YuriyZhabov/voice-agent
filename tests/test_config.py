"""Unit tests for agent configuration module.

Tests loading from environment variables, default values, and validation errors.
Requirements: 5.1, 5.2, 5.3
"""

import os
import pytest
from pydantic import ValidationError

from agent.config import AgentConfig, load_config


@pytest.fixture
def required_env_vars(monkeypatch, tmp_path):
    """Set all required environment variables for testing.
    
    Uses a temporary directory to avoid loading the real .env file.
    """
    # Change to temp dir to avoid loading real .env
    monkeypatch.chdir(tmp_path)
    
    env_vars = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "test-api-key",
        "LIVEKIT_API_SECRET": "test-api-secret",
        "DEEPGRAM_API_KEY": "test-deepgram-key",
        "OPENAI_API_KEY": "test-openai-key",
        "ELEVEN_API_KEY": "test-eleven-key",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


class TestConfigLoadingFromEnv:
    """Test loading configuration from environment variables."""

    def test_loads_required_livekit_vars(self, required_env_vars, monkeypatch):
        """Config loads LiveKit settings from env vars (Req 5.1)."""
        config = AgentConfig()
        
        assert config.livekit_url == "wss://test.livekit.cloud"
        assert config.livekit_api_key == "test-api-key"
        assert config.livekit_api_secret == "test-api-secret"

    def test_loads_system_prompt_from_env(self, required_env_vars, monkeypatch):
        """Config loads system prompt from AGENT_SYSTEM_PROMPT (Req 5.1)."""
        monkeypatch.setenv("AGENT_SYSTEM_PROMPT", "Custom prompt")
        config = AgentConfig()
        
        assert config.agent_system_prompt == "Custom prompt"

    def test_loads_voice_id_from_env(self, required_env_vars, monkeypatch):
        """Config loads voice ID from ELEVENLABS_VOICE_ID (Req 5.2)."""
        monkeypatch.setenv("ELEVENLABS_VOICE_ID", "custom-voice")
        config = AgentConfig()
        
        assert config.elevenlabs_voice_id == "custom-voice"

    def test_loads_n8n_mcp_url_from_env(self, required_env_vars, monkeypatch):
        """Config loads n8n MCP URL from N8N_MCP_URL (Req 5.3)."""
        monkeypatch.setenv("N8N_MCP_URL", "http://localhost:5678/mcp")
        config = AgentConfig()
        
        assert config.n8n_mcp_url == "http://localhost:5678/mcp"

    def test_load_config_function(self, required_env_vars):
        """load_config() returns valid AgentConfig instance."""
        config = load_config()
        
        assert isinstance(config, AgentConfig)
        assert config.livekit_url == "wss://test.livekit.cloud"


class TestConfigDefaultValues:
    """Test default values for optional configuration fields."""

    def test_default_system_prompt(self, required_env_vars):
        """System prompt has Russian default value."""
        config = AgentConfig()
        
        assert config.agent_system_prompt == "Ты полезный голосовой ассистент. Отвечай кратко и по делу."

    def test_default_openai_model(self, required_env_vars):
        """OpenAI model defaults to gpt-4o-mini."""
        config = AgentConfig()
        
        assert config.openai_model == "gpt-4o-mini"

    def test_default_openai_base_url(self, required_env_vars):
        """OpenAI base URL defaults to OpenAI API."""
        config = AgentConfig()
        
        assert config.openai_base_url == "https://api.openai.com/v1"

    def test_default_voice_id(self, required_env_vars):
        """ElevenLabs voice ID defaults to alex."""
        config = AgentConfig()
        
        assert config.elevenlabs_voice_id == "alex"

    def test_default_n8n_mcp_url_is_none(self, required_env_vars):
        """n8n MCP URL defaults to None (optional)."""
        config = AgentConfig()
        
        assert config.n8n_mcp_url is None

    def test_default_silence_timeout(self, required_env_vars):
        """Silence timeout defaults to 60 seconds."""
        config = AgentConfig()
        
        assert config.silence_timeout_seconds == 60

    def test_default_tool_timeout(self, required_env_vars):
        """Tool timeout defaults to 30 seconds."""
        config = AgentConfig()
        
        assert config.tool_timeout_seconds == 30


class TestConfigValidationErrors:
    """Test validation errors for invalid configuration."""

    def test_missing_livekit_url_raises_error(self, monkeypatch, tmp_path):
        """Missing LIVEKIT_URL raises ValidationError."""
        monkeypatch.chdir(tmp_path)  # Avoid loading real .env
        monkeypatch.setenv("LIVEKIT_API_KEY", "key")
        monkeypatch.setenv("LIVEKIT_API_SECRET", "secret")
        monkeypatch.setenv("DEEPGRAM_API_KEY", "key")
        monkeypatch.setenv("OPENAI_API_KEY", "key")
        monkeypatch.setenv("ELEVEN_API_KEY", "key")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "livekit_url" in str(exc_info.value)

    def test_missing_api_keys_raises_error(self, monkeypatch, tmp_path):
        """Missing required API keys raises ValidationError."""
        monkeypatch.chdir(tmp_path)  # Avoid loading real .env
        monkeypatch.setenv("LIVEKIT_URL", "wss://test.livekit.cloud")
        
        with pytest.raises(ValidationError):
            AgentConfig()

    def test_invalid_livekit_url_scheme_raises_error(self, required_env_vars, monkeypatch):
        """LiveKit URL without wss:// or ws:// raises ValidationError."""
        monkeypatch.setenv("LIVEKIT_URL", "https://invalid.url")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "must start with wss:// or ws://" in str(exc_info.value)

    def test_invalid_n8n_mcp_url_scheme_raises_error(self, required_env_vars, monkeypatch):
        """n8n MCP URL without http:// or https:// raises ValidationError."""
        monkeypatch.setenv("N8N_MCP_URL", "ftp://invalid.url")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "must start with http:// or https://" in str(exc_info.value)

    def test_silence_timeout_below_minimum_raises_error(self, required_env_vars, monkeypatch):
        """Silence timeout below 1 second raises ValidationError."""
        monkeypatch.setenv("SILENCE_TIMEOUT_SECONDS", "0")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "silence_timeout_seconds" in str(exc_info.value)

    def test_silence_timeout_above_maximum_raises_error(self, required_env_vars, monkeypatch):
        """Silence timeout above 300 seconds raises ValidationError."""
        monkeypatch.setenv("SILENCE_TIMEOUT_SECONDS", "500")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "silence_timeout_seconds" in str(exc_info.value)

    def test_tool_timeout_below_minimum_raises_error(self, required_env_vars, monkeypatch):
        """Tool timeout below 1 second raises ValidationError."""
        monkeypatch.setenv("TOOL_TIMEOUT_SECONDS", "0")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "tool_timeout_seconds" in str(exc_info.value)


class TestSIPConfigFields:
    """Test SIP telephony configuration fields (Requirements: 1.1, 1.2)."""

    def test_default_sip_trunk_id_is_none(self, required_env_vars):
        """SIP trunk ID defaults to None (optional)."""
        config = AgentConfig()
        assert config.sip_trunk_id is None

    def test_default_sip_phone_number_is_none(self, required_env_vars):
        """SIP phone number defaults to None (optional)."""
        config = AgentConfig()
        assert config.sip_phone_number is None

    def test_default_agent_name(self, required_env_vars):
        """Agent name defaults to voice-agent-mvp."""
        config = AgentConfig()
        assert config.agent_name == "voice-agent-mvp"

    def test_loads_sip_trunk_id_from_env(self, required_env_vars, monkeypatch):
        """Config loads SIP trunk ID from SIP_TRUNK_ID."""
        monkeypatch.setenv("SIP_TRUNK_ID", "ST_test123")
        config = AgentConfig()
        assert config.sip_trunk_id == "ST_test123"

    def test_loads_sip_phone_number_from_env(self, required_env_vars, monkeypatch):
        """Config loads SIP phone number from SIP_PHONE_NUMBER."""
        monkeypatch.setenv("SIP_PHONE_NUMBER", "+79001234567")
        config = AgentConfig()
        assert config.sip_phone_number == "+79001234567"

    def test_loads_agent_name_from_env(self, required_env_vars, monkeypatch):
        """Config loads agent name from AGENT_NAME."""
        monkeypatch.setenv("AGENT_NAME", "custom-agent")
        config = AgentConfig()
        assert config.agent_name == "custom-agent"


class TestExolveConfigFields:
    """Test MTS Exolve configuration fields (Requirements: 1.1, 1.2)."""

    def test_default_exolve_api_key_is_none(self, required_env_vars):
        """Exolve API key defaults to None (optional)."""
        config = AgentConfig()
        assert config.exolve_api_key is None

    def test_default_exolve_sip_resource_id_is_none(self, required_env_vars):
        """Exolve SIP resource ID defaults to None (optional)."""
        config = AgentConfig()
        assert config.exolve_sip_resource_id is None

    def test_default_exolve_phone_number_is_none(self, required_env_vars):
        """Exolve phone number defaults to None (optional)."""
        config = AgentConfig()
        assert config.exolve_phone_number is None

    def test_default_exolve_sip_username_is_none(self, required_env_vars):
        """Exolve SIP username defaults to None (optional)."""
        config = AgentConfig()
        assert config.exolve_sip_username is None

    def test_default_exolve_sip_domain(self, required_env_vars):
        """Exolve SIP domain defaults to sip.exolve.ru."""
        config = AgentConfig()
        assert config.exolve_sip_domain == "sip.exolve.ru"

    def test_loads_exolve_api_key_from_env(self, required_env_vars, monkeypatch):
        """Config loads Exolve API key from EXOLVE_API_KEY."""
        monkeypatch.setenv("EXOLVE_API_KEY", "test-exolve-key")
        config = AgentConfig()
        assert config.exolve_api_key == "test-exolve-key"

    def test_loads_exolve_sip_resource_id_from_env(self, required_env_vars, monkeypatch):
        """Config loads Exolve SIP resource ID from EXOLVE_SIP_RESOURCE_ID."""
        monkeypatch.setenv("EXOLVE_SIP_RESOURCE_ID", "240245")
        config = AgentConfig()
        assert config.exolve_sip_resource_id == "240245"

    def test_loads_exolve_phone_number_from_env(self, required_env_vars, monkeypatch):
        """Config loads Exolve phone number from EXOLVE_PHONE_NUMBER."""
        monkeypatch.setenv("EXOLVE_PHONE_NUMBER", "+79587401087")
        config = AgentConfig()
        assert config.exolve_phone_number == "+79587401087"

    def test_loads_exolve_sip_username_from_env(self, required_env_vars, monkeypatch):
        """Config loads Exolve SIP username from EXOLVE_SIP_USERNAME."""
        monkeypatch.setenv("EXOLVE_SIP_USERNAME", "883140776944348")
        config = AgentConfig()
        assert config.exolve_sip_username == "883140776944348"

    def test_loads_exolve_sip_domain_from_env(self, required_env_vars, monkeypatch):
        """Config loads Exolve SIP domain from EXOLVE_SIP_DOMAIN."""
        monkeypatch.setenv("EXOLVE_SIP_DOMAIN", "custom.sip.domain")
        config = AgentConfig()
        assert config.exolve_sip_domain == "custom.sip.domain"
