"""Voice Agent MVP - Main entry point.

LiveKit Agents SDK based voice agent for handling incoming SIP calls.
Uses Deepgram for STT, OpenAI for LLM, Cartesia for TTS, and Silero for VAD.

Requirements: 1.1, 1.2, 2.1, 2.2, 3.2, 1.4, 3.4
"""

import asyncio
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv
from livekit import api
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, get_job_context, metrics, MetricsCollectedEvent
from livekit.agents import mcp
from livekit.plugins import cartesia, deepgram, groq, openai, silero

from agent.config import load_config
from agent.yandex import create_stt, create_tts, create_llm
from agent.logger import CallLogger
from agent.prompts import get_assistant_prompt
from agent.tools import get_all_tools


@dataclass
class LatencyMetrics:
    """Track latency metrics for the voice pipeline."""
    
    # Timestamps
    user_speech_end: float = 0.0
    stt_complete: float = 0.0
    llm_first_token: float = 0.0
    llm_complete: float = 0.0
    tts_first_audio: float = 0.0
    
    # Calculated latencies (ms)
    stt_latency_ms: float = 0.0
    llm_ttft_ms: float = 0.0  # Time to first token
    llm_total_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0  # User stops speaking → Agent starts speaking
    
    # Aggregates
    turn_count: int = 0
    latencies: list = field(default_factory=list)
    
    def start_turn(self):
        """Mark start of a new turn (user stopped speaking)."""
        self.user_speech_end = time.time()
    
    def mark_stt_complete(self):
        """Mark STT transcription complete."""
        self.stt_complete = time.time()
        if self.user_speech_end > 0:
            self.stt_latency_ms = (self.stt_complete - self.user_speech_end) * 1000
    
    def mark_llm_first_token(self):
        """Mark first LLM token received."""
        self.llm_first_token = time.time()
        if self.stt_complete > 0:
            self.llm_ttft_ms = (self.llm_first_token - self.stt_complete) * 1000
    
    def mark_llm_complete(self):
        """Mark LLM response complete."""
        self.llm_complete = time.time()
        if self.stt_complete > 0:
            self.llm_total_ms = (self.llm_complete - self.stt_complete) * 1000
    
    def mark_tts_first_audio(self):
        """Mark first TTS audio chunk (agent starts speaking)."""
        self.tts_first_audio = time.time()
        if self.llm_first_token > 0:
            self.tts_latency_ms = (self.tts_first_audio - self.llm_first_token) * 1000
        if self.user_speech_end > 0:
            self.total_latency_ms = (self.tts_first_audio - self.user_speech_end) * 1000
            self.latencies.append(self.total_latency_ms)
            self.turn_count += 1
    
    def get_current_turn_metrics(self) -> dict:
        """Get metrics for current turn."""
        return {
            "stt_ms": round(self.stt_latency_ms, 1),
            "llm_ttft_ms": round(self.llm_ttft_ms, 1),
            "llm_total_ms": round(self.llm_total_ms, 1),
            "tts_ms": round(self.tts_latency_ms, 1),
            "total_ms": round(self.total_latency_ms, 1),
        }
    
    def get_summary(self) -> dict:
        """Get summary metrics for the call."""
        if not self.latencies:
            return {"turn_count": 0}
        
        return {
            "turn_count": self.turn_count,
            "avg_latency_ms": round(sum(self.latencies) / len(self.latencies), 1),
            "min_latency_ms": round(min(self.latencies), 1),
            "max_latency_ms": round(max(self.latencies), 1),
            "p50_latency_ms": round(sorted(self.latencies)[len(self.latencies) // 2], 1),
        }

# Load environment variables
load_dotenv()

# Load configuration
config = load_config()

# Create server with explicit agent name for telephony dispatch
server = AgentServer()


class SilenceMonitor:
    """Monitor for user silence and trigger call termination after timeout."""
    
    def __init__(
        self,
        timeout_seconds: float,
        logger: CallLogger,
        on_timeout: callable,
    ):
        self.timeout_seconds = timeout_seconds
        self.logger = logger
        self.on_timeout = on_timeout
        self.last_activity_time = time.time()
        self._task: asyncio.Task | None = None
        self._running = False
    
    def reset(self):
        """Reset the silence timer (called when user speaks)."""
        self.last_activity_time = time.time()
    
    async def start(self):
        """Start monitoring for silence."""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            await asyncio.sleep(1.0)  # Check every second
            
            elapsed = time.time() - self.last_activity_time
            if elapsed >= self.timeout_seconds:
                self.logger.log_event("silence_timeout", {
                    "timeout_seconds": self.timeout_seconds,
                    "elapsed_seconds": elapsed,
                })
                await self.on_timeout()
                break


@server.rtc_session(agent_name=config.agent_name)
async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent.
    
    Called when a new call arrives via SIP or when agent is dispatched to a room.
    Sets up the voice pipeline and starts the conversation.
    """
    await ctx.connect()
    
    # Create logger for this call
    room_name = ctx.room.name if ctx.room else "unknown"
    logger = CallLogger(call_id=room_name)
    logger.log_event("call_started", {"room": room_name})
    
    # Track if call is ending (will be set in agent userdata after agent creation)
    call_state = {"ending": False}
    
    async def handle_silence_timeout():
        """Handle silence timeout - say goodbye and hang up."""
        if call_state["ending"]:
            return
        call_state["ending"] = True
        
        logger.log_event("initiating_goodbye", {"reason": "silence_timeout"})
        
        # Generate farewell message
        await agent_session.generate_reply(
            instructions="Пользователь молчит слишком долго. Вежливо попрощайся и заверши разговор."
        )
        
        # Wait a bit for TTS to finish
        await asyncio.sleep(3.0)
        
        # Hang up the call
        await hangup_call()
    
    # Create silence monitor
    silence_monitor = SilenceMonitor(
        timeout_seconds=config.silence_timeout_seconds,
        logger=logger,
        on_timeout=handle_silence_timeout,
    )
    
    # Initialize latency metrics
    latency_metrics = LatencyMetrics()
    
    # Get all tools from the tools module
    tools = get_all_tools()
    from agent.tools import _get_tool_name
    logger.log_event("tools_loaded", {"count": len(tools), "names": [_get_tool_name(t) for t in tools]})
    
    try:
        # Configure MCP servers
        mcp_servers = []
        
        # Add n8n MCP server if configured
        if config.n8n_mcp_url:
            try:
                mcp_servers.append(mcp.MCPServerHTTP(config.n8n_mcp_url))
                logger.log_event("mcp_configured", {"type": "n8n", "url": config.n8n_mcp_url})
            except Exception as e:
                logger.log_error(e, context={"phase": "n8n_mcp_setup"})
        
        # Note: Smithery MCP servers require OAuth which is not supported in server-side agents
        # Weather functionality is provided via built-in get_weather tool instead
        
        # Set to None if no servers configured
        if not mcp_servers:
            mcp_servers = None
        
        # Load system prompt from file (or use config fallback)
        try:
            system_prompt = get_assistant_prompt()
            logger.log_event("prompt_loaded", {"source": "file", "length": len(system_prompt)})
        except FileNotFoundError:
            system_prompt = config.agent_system_prompt
            logger.log_event("prompt_loaded", {"source": "config", "length": len(system_prompt)})
        
        # Create the agent with system prompt and tools
        agent = Agent(
            instructions=system_prompt,
            tools=tools,
            mcp_servers=mcp_servers,
        )

        # Select providers based on config (supports yandex/deepgram/cartesia/openai/groq)
        
        # STT Provider
        if config.stt_provider == "yandex":
            stt_instance = create_stt(config)
            logger.log_event("stt_provider", {"provider": "yandex", "model": config.yandex_stt_model})
        else:
            stt_instance = deepgram.STT(model="nova-3", language="ru")
            logger.log_event("stt_provider", {"provider": "deepgram", "model": "nova-3"})
        
        # TTS Provider
        if config.tts_provider == "yandex":
            tts_instance = create_tts(config)
            logger.log_event("tts_provider", {"provider": "yandex", "voice": config.yandex_tts_voice})
        else:
            tts_instance = cartesia.TTS(model="sonic-3", voice=config.cartesia_voice_id, language="ru")
            logger.log_event("tts_provider", {"provider": "cartesia", "voice": config.cartesia_voice_id})
        
        # LLM Provider
        if config.llm_provider == "yandex":
            llm_instance = create_llm(config)
            logger.log_event("llm_provider", {"provider": "yandex", "model": config.yandex_llm_model})
        elif config.llm_provider == "groq":
            llm_instance = groq.LLM(model=config.groq_model)
            logger.log_event("llm_provider", {"provider": "groq", "model": config.groq_model})
        else:
            llm_instance = openai.LLM(model=config.openai_model, base_url=config.openai_base_url)
            logger.log_event("llm_provider", {"provider": "openai", "model": config.openai_model})
        
        # Create the agent session with voice pipeline and userdata for state
        agent_session = AgentSession(
            vad=silero.VAD.load(),
            stt=stt_instance,
            llm=llm_instance,
            tts=tts_instance,
            userdata={"call_ending": False, "room_name": room_name},
        )
        
        # Set up event handlers for silence monitoring, interruption handling, and latency tracking
        @agent_session.on("user_started_speaking")
        def on_user_started_speaking():
            """Reset silence timer when user starts speaking."""
            silence_monitor.reset()
            logger.log_event("user_started_speaking", {})
        
        @agent_session.on("user_stopped_speaking")
        def on_user_stopped_speaking():
            """Log when user stops speaking and start latency tracking."""
            latency_metrics.start_turn()
            logger.log_event("user_stopped_speaking", {})
        
        @agent_session.on("agent_started_speaking")
        def on_agent_started_speaking():
            """Log when agent starts speaking and record total latency."""
            latency_metrics.mark_tts_first_audio()
            turn_metrics = latency_metrics.get_current_turn_metrics()
            logger.log_event("agent_started_speaking", {"latency": turn_metrics})
        
        @agent_session.on("agent_stopped_speaking")
        def on_agent_stopped_speaking():
            """Log when agent stops speaking (including interruptions)."""
            logger.log_event("agent_stopped_speaking", {})
        
        @agent_session.on("user_input_transcribed")
        def on_user_input_transcribed(transcript):
            """Reset silence timer and mark STT complete."""
            silence_monitor.reset()
            latency_metrics.mark_stt_complete()
            logger.log_event("user_input_transcribed", {"transcript": str(transcript)[:100]})
        
        # LiveKit SDK built-in metrics (most accurate)
        usage_collector = metrics.UsageCollector()
        
        # Store detailed metrics for each turn
        turn_metrics_list: list[dict] = []
        
        @agent_session.on("metrics_collected")
        def on_metrics_collected(ev: MetricsCollectedEvent):
            """Collect and log LiveKit SDK metrics."""
            usage_collector.collect(ev.metrics)
            
            # Also use built-in logging
            metrics.log_metrics(ev.metrics)
            
            # Log individual metrics with our logger too
            for m in ev.metrics:
                metric_type = type(m).__name__
                if metric_type == "LLMMetrics":
                    turn_data = {
                        "type": "llm",
                        "ttft_ms": round(m.ttft * 1000, 1),
                        "duration_ms": round(m.duration * 1000, 1),
                        "tokens_per_sec": round(m.tokens_per_second, 1),
                        "prompt_tokens": m.prompt_tokens,
                        "completion_tokens": m.completion_tokens,
                    }
                    turn_metrics_list.append(turn_data)
                    logger.log_event("llm_metrics", turn_data)
                elif metric_type == "TTSMetrics":
                    turn_data = {
                        "type": "tts",
                        "ttfb_ms": round(m.ttfb * 1000, 1),
                        "duration_ms": round(m.duration * 1000, 1),
                        "audio_duration_s": round(m.audio_duration, 2),
                        "characters": m.characters_count,
                    }
                    turn_metrics_list.append(turn_data)
                    logger.log_event("tts_metrics", turn_data)
                elif metric_type == "STTMetrics":
                    turn_data = {
                        "type": "stt",
                        "duration_ms": round(m.duration * 1000, 1),
                        "audio_duration_s": round(m.audio_duration, 2),
                    }
                    turn_metrics_list.append(turn_data)
                    logger.log_event("stt_metrics", turn_data)
                elif metric_type == "EOUMetrics":
                    # End of utterance - total latency calculation
                    turn_data = {
                        "type": "eou",
                        "end_of_utterance_delay_ms": round(m.end_of_utterance_delay * 1000, 1),
                        "transcription_delay_ms": round(m.transcription_delay * 1000, 1),
                    }
                    turn_metrics_list.append(turn_data)
                    logger.log_event("eou_metrics", turn_data)
                    
                    # Calculate and log total latency for this turn
                    # Find matching LLM and TTS metrics
                    llm_ttft = next((x["ttft_ms"] for x in turn_metrics_list if x.get("type") == "llm"), 0)
                    tts_ttfb = next((x["ttfb_ms"] for x in turn_metrics_list if x.get("type") == "tts"), 0)
                    total_latency = turn_data["end_of_utterance_delay_ms"] + llm_ttft + tts_ttfb
                    
                    logger.log_event("turn_latency", {
                        "eou_delay_ms": turn_data["end_of_utterance_delay_ms"],
                        "llm_ttft_ms": llm_ttft,
                        "tts_ttfb_ms": tts_ttfb,
                        "total_latency_ms": round(total_latency, 1),
                    })
        
        # Error handling events
        @agent_session.on("error")
        def on_error(error: Exception):
            """Handle errors from the agent session.
            
            Logs errors and attempts recovery where possible.
            STT errors: Ask user to repeat
            LLM errors: Apologize to user
            """
            error_type = type(error).__name__
            logger.log_error(error, context={"error_type": error_type})
            
            # The SDK handles most errors internally, but we log them
            # for monitoring and debugging purposes
        
        # Start the agent session
        await agent_session.start(
            agent=agent,
            room=ctx.room,
        )
        
        logger.log_event("agent_started", {
            "model": config.openai_model,
            "voice_id": config.elevenlabs_voice_id,
            "silence_timeout": config.silence_timeout_seconds,
        })
        
        # Start silence monitoring
        await silence_monitor.start()
        
        # Greet the caller
        await agent_session.generate_reply(
            instructions="Поприветствуй пользователя кратко и спроси чем можешь помочь."
        )
        
        # Keep the session alive until call ends
        # The agent session handles the conversation loop internally
        while not call_state["ending"]:
            await asyncio.sleep(1.0)
        
    except Exception as e:
        logger.log_error(e, context={"phase": "agent_session"})
        
        # Try to apologize to user if possible
        try:
            if agent_session:
                await agent_session.generate_reply(
                    instructions="Произошла техническая ошибка. Извинись перед пользователем и попроси перезвонить позже."
                )
                await asyncio.sleep(3.0)
        except Exception:
            pass  # Can't recover, just log and exit
        
        raise
    finally:
        # Cleanup resources
        await silence_monitor.stop()
        
        # Log latency summary
        latency_summary = latency_metrics.get_summary()
        logger.log_event("latency_summary", latency_summary)
        
        # Log usage summary from LiveKit SDK
        try:
            usage_summary = usage_collector.get_summary()
            logger.log_event("usage_summary", {
                "llm_prompt_tokens": usage_summary.llm_prompt_tokens,
                "llm_completion_tokens": usage_summary.llm_completion_tokens,
                "tts_characters": usage_summary.tts_characters_count,
                "stt_audio_duration_s": round(usage_summary.stt_audio_duration, 2),
            })
        except Exception:
            pass  # Usage collector may not have data
        
        logger.log_event("call_cleanup", {"room": room_name})
        logger.log_summary()


async def hangup_call():
    """End the call by deleting the room.
    
    Can be called from within the agent to terminate the call gracefully.
    """
    ctx = get_job_context()
    if ctx is None:
        return
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(room=ctx.room.name)
    )


if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)
