"""Provider factory for creating STT, TTS, and LLM instances.

Selects between Yandex Cloud and original providers based on configuration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from livekit.agents import stt, tts, llm
    from agent.config import AgentConfig

logger = logging.getLogger(__name__)


def create_stt(config: "AgentConfig") -> "stt.STT":
    """Create STT provider based on configuration.
    
    Args:
        config: Agent configuration with provider settings
    
    Returns:
        STT instance (YandexSTT or Deepgram)
    """
    if config.stt_provider == "yandex":
        from agent.yandex.stt import YandexSTT
        from agent.yandex.credentials import YandexCredentials
        
        logger.info("Using Yandex SpeechKit STT")
        return YandexSTT(
            credentials=YandexCredentials.from_env(),
            language=config.yandex_stt_language,
            model=config.yandex_stt_model,
        )
    else:
        from livekit.plugins import deepgram
        
        logger.info("Using Deepgram STT")
        return deepgram.STT(model="nova-3")


def create_tts(config: "AgentConfig") -> "tts.TTS":
    """Create TTS provider based on configuration.
    
    Args:
        config: Agent configuration with provider settings
    
    Returns:
        TTS instance (YandexTTS wrapped in StreamAdapter, or Cartesia)
    """
    if config.tts_provider == "yandex":
        from agent.yandex.tts import YandexTTS
        from agent.yandex.credentials import YandexCredentials
        from livekit.agents.tts import StreamAdapter
        from livekit.agents import tokenize
        
        logger.info("Using Yandex SpeechKit TTS")
        base_tts = YandexTTS(
            credentials=YandexCredentials.from_env(),
            voice=config.yandex_tts_voice,
            role=config.yandex_tts_role,
            speed=config.yandex_tts_speed,
            sample_rate=config.yandex_tts_sample_rate,
        )
        # Wrap in StreamAdapter for streaming support
        return StreamAdapter(
            tts=base_tts,
            sentence_tokenizer=tokenize.basic.SentenceTokenizer(),
        )
    else:
        from livekit.plugins import cartesia
        
        logger.info("Using Cartesia TTS")
        return cartesia.TTS()


def create_llm(config: "AgentConfig") -> "llm.LLM":
    """Create LLM provider based on configuration.
    
    Args:
        config: Agent configuration with provider settings
    
    Returns:
        LLM instance (YandexLLM or OpenAI)
    """
    if config.llm_provider == "yandex":
        from agent.yandex.llm import YandexLLM
        from agent.yandex.credentials import YandexCredentials
        
        logger.info("Using YandexGPT LLM")
        return YandexLLM(
            credentials=YandexCredentials.from_env(),
            model=config.yandex_llm_model,
            temperature=config.yandex_llm_temperature,
        )
    else:
        from livekit.plugins import openai
        
        logger.info("Using OpenAI LLM")
        return openai.LLM(model=config.openai_model)
