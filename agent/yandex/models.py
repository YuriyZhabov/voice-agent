"""Pydantic models for Yandex Cloud services configuration.

Provides validated configuration models for LLM, TTS, and STT services.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LLMOptions(BaseModel):
    """Configuration options for YandexGPT LLM.
    
    Attributes:
        model: YandexGPT model name
        temperature: Sampling temperature (0.0 - 1.0)
        max_tokens: Maximum tokens in response
    """
    
    model: str = Field(
        default="yandexgpt-lite",
        description="Model name: yandexgpt-lite, yandexgpt, yandexgpt-32k",
    )
    temperature: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=8192,
        description="Maximum tokens in response",
    )
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model name."""
        valid_models = {"yandexgpt-lite", "yandexgpt", "yandexgpt-32k"}
        if v not in valid_models:
            # Allow custom model URIs
            if not v.startswith("gpt://"):
                pass  # Just warn, don't fail
        return v


class TTSOptions(BaseModel):
    """Configuration options for Yandex SpeechKit TTS.
    
    Attributes:
        voice: Voice name (alena, filipp, ermil, jane, madirus, omazh, zahar)
        role: Voice emotion/role
        speed: Speech speed multiplier
        sample_rate: Audio sample rate in Hz
        format: Audio output format
    """
    
    voice: str = Field(
        default="alena",
        description="Voice name",
    )
    role: str = Field(
        default="neutral",
        description="Voice emotion: neutral, good, evil",
    )
    speed: float = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="Speech speed multiplier",
    )
    sample_rate: int = Field(
        default=22050,
        description="Audio sample rate in Hz",
    )
    format: Literal["lpcm", "oggopus"] = Field(
        default="lpcm",
        description="Audio output format",
    )
    
    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: int) -> int:
        """Validate sample rate is supported."""
        valid_rates = {8000, 16000, 22050, 48000}
        if v not in valid_rates:
            raise ValueError(f"Sample rate must be one of {valid_rates}")
        return v
    
    @field_validator("voice")
    @classmethod
    def validate_voice(cls, v: str) -> str:
        """Validate voice name."""
        valid_voices = {"alena", "filipp", "ermil", "jane", "madirus", "omazh", "zahar"}
        if v not in valid_voices:
            # Allow custom voices, just warn
            pass
        return v


class STTOptions(BaseModel):
    """Configuration options for Yandex SpeechKit STT.
    
    Attributes:
        language: Recognition language code
        model: Recognition model name
        profanity_filter: Enable profanity filtering
        sample_rate: Audio sample rate in Hz
    """
    
    language: str = Field(
        default="ru-RU",
        description="Recognition language code",
    )
    model: str = Field(
        default="general",
        description="Recognition model: general, general:rc",
    )
    profanity_filter: bool = Field(
        default=True,
        description="Filter profanity in results",
    )
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz",
    )
    
    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: int) -> int:
        """Validate sample rate is supported."""
        valid_rates = {8000, 16000, 48000}
        if v not in valid_rates:
            raise ValueError(f"Sample rate must be one of {valid_rates}")
        return v
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code format."""
        if not v or len(v) < 2:
            raise ValueError("Invalid language code")
        return v
