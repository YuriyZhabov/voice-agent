"""Agent configuration module using Pydantic Settings.

Loads configuration from environment variables with validation.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """Agent configuration from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # LiveKit (required)
    livekit_url: str = Field(
        ...,
        description="LiveKit server WebSocket URL",
        examples=["wss://your-server.livekit.cloud"],
    )
    livekit_api_key: str = Field(..., description="LiveKit API key")
    livekit_api_secret: str = Field(..., description="LiveKit API secret")
    
    # Agent Configuration
    agent_system_prompt: str = Field(
        default="Ты полезный голосовой ассистент. Отвечай кратко и по делу.",
        description="System prompt for the agent",
    )
    agent_name: str = Field(
        default="voice-agent",
        description="Agent name for LiveKit dispatch rules",
    )
    
    # n8n MCP Integration (optional)
    n8n_mcp_url: str | None = Field(
        default=None,
        description="n8n MCP server URL for tool integration",
    )
    
    # Timeouts
    silence_timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Seconds of silence before ending call",
    )
    tool_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Timeout for tool execution in seconds",
    )
    
    # ============================================
    # Yandex Cloud Configuration
    # ============================================
    
    # Yandex Cloud Authentication
    yc_api_key: str | None = Field(
        default=None,
        alias="YANDEX_API_KEY",
        description="Yandex Cloud API key",
    )
    yc_folder_id: str | None = Field(
        default=None,
        alias="YANDEX_FOLDER_ID",
        description="Yandex Cloud folder ID (required for billing)",
    )
    
    # SpeechKit STT Configuration
    yandex_stt_model: str = Field(
        default="general",
        description="SpeechKit STT model: 'general', 'general:rc'",
    )
    yandex_stt_language: str = Field(
        default="ru-RU",
        description="SpeechKit STT language code",
    )
    
    # SpeechKit TTS Configuration
    yandex_tts_voice: str = Field(
        default="alena",
        description="SpeechKit TTS voice: 'alena', 'filipp', 'ermil', 'jane', etc.",
    )
    yandex_tts_role: str = Field(
        default="neutral",
        description="SpeechKit TTS role: 'neutral', 'good', 'evil'",
    )
    yandex_tts_speed: float = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="SpeechKit TTS speed (0.1-3.0)",
    )
    yandex_tts_sample_rate: int = Field(
        default=22050,
        description="SpeechKit TTS sample rate: 8000, 16000, 22050, 48000",
    )
    
    # YandexGPT Configuration
    yandex_llm_model: str = Field(
        default="yandexgpt",
        description="YandexGPT model: 'yandexgpt-lite' or 'yandexgpt'",
    )
    yandex_llm_temperature: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="YandexGPT temperature (0.0-1.0)",
    )
    
    @field_validator("livekit_url")
    @classmethod
    def validate_livekit_url(cls, v: str) -> str:
        """Validate LiveKit URL starts with wss:// or ws://."""
        if not v.startswith(("wss://", "ws://")):
            raise ValueError("LiveKit URL must start with wss:// or ws://")
        return v
    
    @field_validator("n8n_mcp_url")
    @classmethod
    def validate_n8n_mcp_url(cls, v: str | None) -> str | None:
        """Validate n8n MCP URL if provided."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("n8n MCP URL must start with http:// or https://")
        return v


def load_config(env_file: str = ".env") -> AgentConfig:
    """Load and validate agent configuration from environment."""
    return AgentConfig(_env_file=env_file)
