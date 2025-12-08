"""Agent configuration module using Pydantic Settings.

Loads configuration from environment variables with validation.
Requirements: 5.1, 5.2, 5.3
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """Agent configuration from environment variables.
    
    All required fields must be set via environment variables or .env file.
    Optional fields have sensible defaults.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # LiveKit (required) - Requirements: 5.1
    livekit_url: str = Field(
        ...,
        description="LiveKit server WebSocket URL",
        examples=["wss://your-server.livekit.cloud"],
    )
    livekit_api_key: str = Field(
        ...,
        description="LiveKit API key",
    )
    livekit_api_secret: str = Field(
        ...,
        description="LiveKit API secret",
    )
    
    # Agent Configuration - Requirements: 5.1
    agent_system_prompt: str = Field(
        default="Ты полезный голосовой ассистент. Отвечай кратко и по делу.",
        description="System prompt for the agent",
    )
    
    # STT - Deepgram (required)
    deepgram_api_key: str = Field(
        ...,
        description="Deepgram API key for speech-to-text",
    )
    
    # LLM Provider Selection
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: 'inference' (LiveKit), 'groq', or 'openai'",
    )
    
    # LLM - LiveKit Inference (recommended for lowest latency)
    inference_model: str = Field(
        default="openai/gpt-4.1-mini",
        description="LiveKit Inference model ID (e.g., openai/gpt-4.1-mini, moonshotai/kimi-k2-instruct)",
    )
    
    # LLM - OpenAI-compatible API (required if llm_provider=openai)
    openai_api_key: str = Field(
        default="",
        description="OpenAI-compatible API key (e.g., CometAPI)",
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI-compatible API base URL",
        examples=["https://api.cometapi.com/v1", "https://api.openai.com/v1"],
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="Model to use (e.g., gpt-4o-mini)",
    )
    
    # LLM - Groq (required if llm_provider=groq)
    groq_api_key: str = Field(
        default="",
        description="Groq API key for fast LLM inference",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use",
    )

    # TTS - ElevenLabs (required) - Requirements: 5.2
    eleven_api_key: str = Field(
        ...,
        description="ElevenLabs API key for text-to-speech",
    )
    elevenlabs_voice_id: str = Field(
        default="alex",
        description="ElevenLabs voice ID to use",
    )
    
    # n8n MCP Integration (optional) - Requirements: 5.3
    n8n_mcp_url: str | None = Field(
        default=None,
        description="n8n MCP server URL for tool integration",
        examples=["http://localhost:5678/mcp"],
    )
    
    # SIP Telephony - LiveKit (optional) - Requirements: 1.1, 1.2
    sip_trunk_id: str | None = Field(
        default=None,
        description="LiveKit SIP trunk ID for incoming calls",
    )
    sip_phone_number: str | None = Field(
        default=None,
        description="Phone number for incoming SIP calls (+7XXXXXXXXXX)",
    )
    agent_name: str = Field(
        default="voice-agent-mvp",
        description="Agent name for LiveKit dispatch rules",
    )
    
    # MTS Exolve Configuration (optional) - Requirements: 1.1, 1.2
    exolve_api_key: str | None = Field(
        default=None,
        description="MTS Exolve API key from dev.exolve.ru",
    )
    exolve_sip_resource_id: str | None = Field(
        default=None,
        description="MTS Exolve SIP resource ID",
    )
    exolve_phone_number: str | None = Field(
        default=None,
        description="MTS Exolve phone number (+7XXXXXXXXXX)",
    )
    exolve_sip_username: str | None = Field(
        default=None,
        description="MTS Exolve SIP username (format: 883140XXXXXXXXXX)",
    )
    exolve_sip_domain: str = Field(
        default="sip.exolve.ru",
        description="MTS Exolve SIP domain",
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
    """Load and validate agent configuration from environment.
    
    Args:
        env_file: Path to .env file (default: ".env")
    
    Returns:
        AgentConfig: Validated configuration object.
        
    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    return AgentConfig(_env_file=env_file)
