"""Unit tests for agent configuration module.

Tests loading from environment variables, default values, and validation errors.
"""

import pytest
from pydantic import ValidationError

from agent.config import AgentConfig, load_config


@pytest.fixture
def required_env_vars(monkeypatch, tmp_path):
    """Set all required environment variables for testing."""
    monkeypatch.chdir(tmp_path)
    
    env_vars = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "test-api-key",
        "LIVEKIT_API_SECRET": "test-api-secret",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


class TestConfigLoadingFromEnv:
    """Test loading configuration from environment variables."""

    def test_loads_required_livekit_vars(self, required_env_vars):
        """Config loads LiveKit settings from env vars."""
        config = AgentConfig()
        
        assert config.livekit_url == "wss://test.livekit.cloud"
        assert config.livekit_api_key == "test-api-key"
        assert config.livekit_api_secret == "test-api-secret"

    def test_loads_system_prompt_from_env(self, required_env_vars, monkeypatch):
        """Config loads system prompt from AGENT_SYSTEM_PROMPT."""
        monkeypatch.setenv("AGENT_SYSTEM_PROMPT", "Custom prompt")
        config = AgentConfig()
        
        assert config.agent_system_prompt == "Custom prompt"

    def test_loads_n8n_mcp_url_from_env(self, required_env_vars, monkeypatch):
        """Config loads n8n MCP URL from N8N_MCP_URL."""
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

    def test_default_agent_name(self, required_env_vars):
        """Agent name defaults to voice-agent."""
        config = AgentConfig()
        
        assert config.agent_name == "voice-agent"

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


class TestYandexConfigFields:
    """Test Yandex Cloud configuration fields."""

    def test_default_yandex_llm_model(self, required_env_vars):
        """YandexGPT model defaults to yandexgpt."""
        config = AgentConfig()
        assert config.yandex_llm_model == "yandexgpt"

    def test_default_yandex_tts_voice(self, required_env_vars):
        """Yandex TTS voice defaults to alena."""
        config = AgentConfig()
        assert config.yandex_tts_voice == "alena"

    def test_default_yandex_stt_language(self, required_env_vars):
        """Yandex STT language defaults to ru-RU."""
        config = AgentConfig()
        assert config.yandex_stt_language == "ru-RU"

    def test_loads_yandex_api_key_from_env(self, required_env_vars, monkeypatch):
        """Config loads Yandex API key from YANDEX_API_KEY."""
        monkeypatch.setenv("YANDEX_API_KEY", "test-yandex-key")
        config = AgentConfig()
        assert config.yc_api_key == "test-yandex-key"

    def test_loads_yandex_folder_id_from_env(self, required_env_vars, monkeypatch):
        """Config loads Yandex folder ID from YANDEX_FOLDER_ID."""
        monkeypatch.setenv("YANDEX_FOLDER_ID", "b1g12345")
        config = AgentConfig()
        assert config.yc_folder_id == "b1g12345"


class TestConfigValidationErrors:
    """Test validation errors for invalid configuration."""

    def test_missing_livekit_url_raises_error(self, monkeypatch, tmp_path):
        """Missing LIVEKIT_URL raises ValidationError."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("LIVEKIT_URL", raising=False)
        monkeypatch.setenv("LIVEKIT_API_KEY", "key")
        monkeypatch.setenv("LIVEKIT_API_SECRET", "secret")
        
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig()
        
        assert "livekit_url" in str(exc_info.value)

    def test_missing_api_keys_raises_error(self, monkeypatch, tmp_path):
        """Missing required API keys raises ValidationError."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("LIVEKIT_API_KEY", raising=False)
        monkeypatch.delenv("LIVEKIT_API_SECRET", raising=False)
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
