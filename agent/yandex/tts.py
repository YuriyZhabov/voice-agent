"""Yandex SpeechKit TTS plugin for LiveKit Agents.

Implements streaming speech synthesis using SpeechKit API v3 via gRPC.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

import grpc

from livekit import rtc
from livekit.agents import tts, APIConnectOptions

from agent.yandex.credentials import YandexCredentials

logger = logging.getLogger(__name__)

# SpeechKit gRPC endpoints
TTS_ENDPOINT = "tts.api.cloud.yandex.net:443"


@dataclass
class _TTSOptions:
    """Internal options for TTS configuration."""
    voice: str
    role: str
    speed: float
    sample_rate: int
    format: str


class YandexTTS(tts.TTS):
    """SpeechKit TTS plugin for LiveKit Agents.
    
    Provides streaming speech synthesis using Yandex SpeechKit API v3.
    """
    
    def __init__(
        self,
        *,
        credentials: YandexCredentials | None = None,
        voice: str = "alena",
        role: str = "neutral",
        speed: float = 1.0,
        sample_rate: int = 22050,
        audio_format: str = "lpcm",
    ) -> None:
        """Initialize YandexTTS.
        
        Args:
            credentials: Yandex Cloud credentials (loads from env if None)
            voice: Voice name (alena, filipp, ermil, jane, madirus, omazh, zahar)
            role: Voice role/emotion (neutral, good, evil)
            speed: Speech speed (0.1 - 3.0)
            sample_rate: Audio sample rate (8000, 16000, 22050, 48000)
            audio_format: Output format (lpcm, oggopus)
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=True,
            ),
            sample_rate=sample_rate,
            num_channels=1,
        )
        
        self._credentials = credentials or YandexCredentials.from_env()
        self._opts = _TTSOptions(
            voice=voice,
            role=role,
            speed=speed,
            sample_rate=sample_rate,
            format=audio_format,
        )
    
    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = APIConnectOptions(),
    ) -> "YandexTTSStream":
        """Synthesize text to speech.
        
        Args:
            text: Text to synthesize (can include SSML markup)
            conn_options: Connection options
        
        Returns:
            YandexTTSStream for streaming audio output
        """
        return YandexTTSStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            credentials=self._credentials,
            opts=self._opts,
        )


class YandexTTSStream(tts.ChunkedStream):
    """Streaming TTS using SpeechKit gRPC API v3."""
    
    def __init__(
        self,
        *,
        tts: YandexTTS,
        input_text: str,
        conn_options: APIConnectOptions,
        credentials: YandexCredentials,
        opts: _TTSOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._credentials = credentials
        self._opts = opts
        self._channel: grpc.aio.Channel | None = None
    
    async def _run(self) -> None:
        """Stream synthesized audio chunks."""
        try:
            from yandex.cloud.ai.tts.v3 import tts_service_pb2_grpc
            from yandex.cloud.ai.tts.v3 import tts_pb2
        except ImportError as e:
            logger.error(
                "Failed to import SpeechKit TTS gRPC stubs. "
                "Run: pip install yandexcloud"
            )
            raise ImportError(
                "SpeechKit TTS gRPC stubs not found. Install yandexcloud package."
            ) from e
        
        # Create secure gRPC channel
        ssl_creds = grpc.ssl_channel_credentials()
        self._channel = grpc.aio.secure_channel(TTS_ENDPOINT, ssl_creds)
        
        try:
            stub = tts_service_pb2_grpc.SynthesizerStub(self._channel)
            
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Build request
            request = tts_pb2.UtteranceSynthesisRequest(
                text=self._input_text,
                output_audio_spec=tts_pb2.AudioFormatOptions(
                    raw_audio=tts_pb2.RawAudio(
                        audio_encoding=tts_pb2.RawAudio.LINEAR16_PCM,
                        sample_rate_hertz=self._opts.sample_rate,
                    )
                ),
                hints=[
                    tts_pb2.Hints(voice=self._opts.voice),
                    tts_pb2.Hints(role=self._opts.role),
                    tts_pb2.Hints(speed=self._opts.speed),
                ],
                loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS,
            )
            
            # Stream response
            metadata = self._credentials.get_grpc_metadata()
            responses = stub.UtteranceSynthesis(request, metadata=metadata)
            
            async for response in responses:
                if response.HasField("audio_chunk"):
                    audio_data = response.audio_chunk.data
                    
                    # Calculate samples per channel (16-bit audio = 2 bytes per sample)
                    samples_per_channel = len(audio_data) // 2
                    
                    # Create AudioFrame
                    audio_frame = rtc.AudioFrame(
                        data=audio_data,
                        sample_rate=self._opts.sample_rate,
                        num_channels=1,
                        samples_per_channel=samples_per_channel,
                    )
                    
                    # Create SynthesizedAudio event
                    synth_audio = tts.SynthesizedAudio(
                        frame=audio_frame,
                        request_id=request_id,
                    )
                    self._event_ch.send_nowait(synth_audio)
                    
        except grpc.aio.AioRpcError as e:
            logger.error(f"SpeechKit TTS error: {e.code()} - {e.details()}")
            raise
        finally:
            if self._channel:
                await self._channel.close()
