"""Yandex SpeechKit STT plugin for LiveKit Agents.

Implements streaming speech recognition using SpeechKit API v3 via gRPC.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import grpc

from livekit.agents import stt, utils

from agent.yandex.credentials import YandexCredentials

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

# SpeechKit gRPC endpoints
STT_ENDPOINT = "stt.api.cloud.yandex.net:443"


@dataclass
class _STTOptions:
    """Internal options for STT configuration."""
    language: str
    model: str
    profanity_filter: bool
    sample_rate: int


class YandexSTT(stt.STT):
    """SpeechKit STT plugin for LiveKit Agents.
    
    Provides streaming speech recognition using Yandex SpeechKit API v3.
    
    Example:
        >>> from agent.yandex import YandexCredentials
        >>> from agent.yandex.stt import YandexSTT
        >>> 
        >>> creds = YandexCredentials.from_env()
        >>> stt = YandexSTT(credentials=creds)
        >>> 
        >>> # Use in AgentSession
        >>> session = AgentSession(stt=stt, ...)
    """
    
    def __init__(
        self,
        *,
        credentials: YandexCredentials | None = None,
        language: str = "ru-RU",
        model: str = "general",
        profanity_filter: bool = True,
        sample_rate: int = 16000,
    ) -> None:
        """Initialize YandexSTT.
        
        Args:
            credentials: Yandex Cloud credentials (loads from env if None)
            language: Recognition language (default: ru-RU)
            model: Recognition model (general, general:rc)
            profanity_filter: Filter profanity in results
            sample_rate: Audio sample rate in Hz (8000, 16000, 48000)
        """
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=True,
                interim_results=True,
            )
        )
        
        self._credentials = credentials or YandexCredentials.from_env()
        self._opts = _STTOptions(
            language=language,
            model=model,
            profanity_filter=profanity_filter,
            sample_rate=sample_rate,
        )
    
    def stream(
        self,
        *,
        language: str | None = None,
    ) -> YandexSTTStream:
        """Create a streaming recognition session.
        
        Args:
            language: Override default language for this session
        
        Returns:
            YandexSTTStream instance for streaming recognition
        """
        opts = _STTOptions(
            language=language or self._opts.language,
            model=self._opts.model,
            profanity_filter=self._opts.profanity_filter,
            sample_rate=self._opts.sample_rate,
        )
        return YandexSTTStream(
            stt=self,
            credentials=self._credentials,
            opts=opts,
        )


class YandexSTTStream(stt.SpeechStream):
    """Streaming STT session using SpeechKit gRPC API v3.
    
    Handles bidirectional streaming: sends audio chunks, receives transcriptions.
    """
    
    def __init__(
        self,
        *,
        stt: YandexSTT,
        credentials: YandexCredentials,
        opts: _STTOptions,
    ) -> None:
        super().__init__(stt=stt)
        self._credentials = credentials
        self._opts = opts
        self._channel: grpc.aio.Channel | None = None
        self._reconnect_event = asyncio.Event()
        self._session_start_time: float = 0
        
    async def _run(self) -> None:
        """Main streaming loop.
        
        1. Establishes gRPC connection
        2. Sends session options
        3. Streams audio chunks
        4. Yields SpeechEvents for results
        """
        try:
            # Import gRPC stubs (generated from proto)
            # Note: These need to be generated from yandex-cloud/cloudapi protos
            from yandex.cloud.ai.stt.v3 import stt_service_pb2_grpc
            from yandex.cloud.ai.stt.v3 import stt_pb2
        except ImportError as e:
            logger.error(
                "Failed to import SpeechKit gRPC stubs. "
                "Run: pip install yandexcloud grpcio-tools"
            )
            raise ImportError(
                "SpeechKit gRPC stubs not found. Install yandexcloud package."
            ) from e
        
        self._session_start_time = time.time()
        
        # Create secure gRPC channel
        ssl_creds = grpc.ssl_channel_credentials()
        self._channel = grpc.aio.secure_channel(STT_ENDPOINT, ssl_creds)
        
        try:
            stub = stt_service_pb2_grpc.RecognizerStub(self._channel)
            
            # Create request generator
            async def request_generator() -> AsyncIterator:
                # First message: session options
                session_options = stt_pb2.StreamingRequest(
                    session_options=stt_pb2.StreamingOptions(
                        recognition_model=stt_pb2.RecognitionModelOptions(
                            model=self._opts.model,
                            audio_format=stt_pb2.AudioFormatOptions(
                                raw_audio=stt_pb2.RawAudio(
                                    audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
                                    sample_rate_hertz=self._opts.sample_rate,
                                    audio_channel_count=1,
                                )
                            ),
                            text_normalization=stt_pb2.TextNormalizationOptions(
                                text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                                profanity_filter=self._opts.profanity_filter,
                            ),
                            language_restriction=stt_pb2.LanguageRestrictionOptions(
                                restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                                language_code=[self._opts.language],
                            ),
                        ),
                    )
                )
                yield session_options
                
                # Stream audio chunks
                async for frame in self._input_ch:
                    if isinstance(frame, self._FlushSentinel):
                        continue
                    
                    chunk = stt_pb2.StreamingRequest(
                        chunk=stt_pb2.AudioChunk(data=frame.data.tobytes())
                    )
                    yield chunk
                    
                    # Check session duration (5 min limit)
                    if time.time() - self._session_start_time > 290:  # 4:50
                        logger.warning("STT session approaching 5 min limit, reconnecting...")
                        self._reconnect_event.set()
                        break
            
            # Start bidirectional streaming
            metadata = self._credentials.get_grpc_metadata()
            responses = stub.RecognizeStreaming(
                request_generator(),
                metadata=metadata,
            )
            
            # Process responses
            async for response in responses:
                event = self._convert_response(response)
                if event:
                    self._event_ch.send_nowait(event)
                    
        except grpc.aio.AioRpcError as e:
            logger.error(f"SpeechKit STT error: {e.code()} - {e.details()}")
            raise
        finally:
            if self._channel:
                await self._channel.close()
    
    def _convert_response(self, response) -> stt.SpeechEvent | None:
        """Convert SpeechKit response to LiveKit SpeechEvent."""
        # Check response type
        if not response.HasField("final") and not response.HasField("partial"):
            return None
        
        is_final = response.HasField("final")
        
        if is_final:
            alternatives_data = response.final.alternatives
        else:
            alternatives_data = response.partial.alternatives
        
        if not alternatives_data:
            return None
        
        alternatives = [
            stt.SpeechData(
                text=alt.text,
                confidence=alt.confidence if hasattr(alt, 'confidence') else 1.0,
                language=self._opts.language,
            )
            for alt in alternatives_data
        ]
        
        event_type = (
            stt.SpeechEventType.FINAL_TRANSCRIPT
            if is_final
            else stt.SpeechEventType.INTERIM_TRANSCRIPT
        )
        
        return stt.SpeechEvent(
            type=event_type,
            alternatives=alternatives,
        )
