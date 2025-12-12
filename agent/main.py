"""Voice Agent - Main entry point.

LiveKit Agents SDK based voice agent using Yandex Cloud services:
- YandexGPT for LLM
- SpeechKit for STT/TTS
- Silero for VAD
"""

import asyncio
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    get_job_context,
    metrics,
    MetricsCollectedEvent,
)
from livekit.agents import mcp
from livekit.plugins import silero

from agent.config import load_config
from agent.yandex import create_stt, create_tts, create_llm
from agent.logger import CallLogger
from agent.prompts import get_assistant_prompt
from agent.tools import get_all_tools


@dataclass
class LatencyMetrics:
    """Track latency metrics for the voice pipeline."""
    
    user_speech_end: float = 0.0
    stt_complete: float = 0.0
    llm_first_token: float = 0.0
    tts_first_audio: float = 0.0
    total_latency_ms: float = 0.0
    turn_count: int = 0
    latencies: list = field(default_factory=list)
    
    def start_turn(self):
        self.user_speech_end = time.time()
    
    def mark_stt_complete(self):
        self.stt_complete = time.time()
    
    def mark_tts_first_audio(self):
        self.tts_first_audio = time.time()
        if self.user_speech_end > 0:
            self.total_latency_ms = (self.tts_first_audio - self.user_speech_end) * 1000
            self.latencies.append(self.total_latency_ms)
            self.turn_count += 1
    
    def get_summary(self) -> dict:
        if not self.latencies:
            return {"turn_count": 0}
        return {
            "turn_count": self.turn_count,
            "avg_latency_ms": round(sum(self.latencies) / len(self.latencies), 1),
            "min_latency_ms": round(min(self.latencies), 1),
            "max_latency_ms": round(max(self.latencies), 1),
        }


load_dotenv()
config = load_config()
server = AgentServer()


class SilenceMonitor:
    """Monitor for user silence and trigger call termination after timeout."""
    
    def __init__(self, timeout_seconds: float, logger: CallLogger, on_timeout: callable):
        self.timeout_seconds = timeout_seconds
        self.logger = logger
        self.on_timeout = on_timeout
        self.last_activity_time = time.time()
        self._task: asyncio.Task | None = None
        self._running = False
    
    def reset(self):
        self.last_activity_time = time.time()
    
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        while self._running:
            await asyncio.sleep(1.0)
            elapsed = time.time() - self.last_activity_time
            if elapsed >= self.timeout_seconds:
                self.logger.log_event("silence_timeout", {"elapsed_seconds": elapsed})
                await self.on_timeout()
                break


@server.rtc_session(agent_name=config.agent_name)
async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent."""
    await ctx.connect()
    
    room_name = ctx.room.name if ctx.room else "unknown"
    logger = CallLogger(call_id=room_name)
    logger.log_event("call_started", {"room": room_name})
    
    call_state = {"ending": False}
    agent_session = None
    
    async def handle_silence_timeout():
        if call_state["ending"]:
            return
        call_state["ending"] = True
        logger.log_event("initiating_goodbye", {"reason": "silence_timeout"})
        
        if agent_session:
            await agent_session.generate_reply(
                instructions="Пользователь молчит слишком долго. Вежливо попрощайся и заверши разговор."
            )
            await asyncio.sleep(3.0)
        await hangup_call()
    
    silence_monitor = SilenceMonitor(
        timeout_seconds=config.silence_timeout_seconds,
        logger=logger,
        on_timeout=handle_silence_timeout,
    )
    latency_metrics = LatencyMetrics()
    
    tools = get_all_tools()
    from agent.tools import _get_tool_name
    logger.log_event("tools_loaded", {"count": len(tools), "names": [_get_tool_name(t) for t in tools]})
    
    try:
        # Configure MCP servers
        mcp_servers = []
        if config.n8n_mcp_url:
            try:
                mcp_servers.append(mcp.MCPServerHTTP(config.n8n_mcp_url))
                logger.log_event("mcp_configured", {"url": config.n8n_mcp_url})
            except Exception as e:
                logger.log_error(e, context={"phase": "mcp_setup"})
        
        # Load system prompt
        try:
            system_prompt = get_assistant_prompt()
            logger.log_event("prompt_loaded", {"source": "file", "length": len(system_prompt)})
        except FileNotFoundError:
            system_prompt = config.agent_system_prompt
            logger.log_event("prompt_loaded", {"source": "config"})
        
        # Create agent with Yandex services
        agent = Agent(
            instructions=system_prompt,
            tools=tools,
            mcp_servers=mcp_servers if mcp_servers else None,
        )
        
        stt_instance = create_stt(config)
        tts_instance = create_tts(config)
        llm_instance = create_llm(config)
        
        logger.log_event("providers", {
            "stt": "yandex",
            "tts": "yandex", 
            "llm": "yandex",
            "model": config.yandex_llm_model,
        })
        
        agent_session = AgentSession(
            vad=silero.VAD.load(),
            stt=stt_instance,
            llm=llm_instance,
            tts=tts_instance,
            userdata={"call_ending": False, "room_name": room_name},
        )
        
        @agent_session.on("user_started_speaking")
        def on_user_started_speaking():
            silence_monitor.reset()
        
        @agent_session.on("user_stopped_speaking")
        def on_user_stopped_speaking():
            latency_metrics.start_turn()
        
        @agent_session.on("agent_started_speaking")
        def on_agent_started_speaking():
            latency_metrics.mark_tts_first_audio()
            logger.log_event("turn_latency", {"total_ms": round(latency_metrics.total_latency_ms, 1)})
        
        @agent_session.on("user_input_transcribed")
        def on_user_input_transcribed(transcript):
            silence_monitor.reset()
            latency_metrics.mark_stt_complete()
            logger.log_event("transcribed", {"text": str(transcript)[:100]})
        
        usage_collector = metrics.UsageCollector()
        
        @agent_session.on("metrics_collected")
        def on_metrics_collected(ev: MetricsCollectedEvent):
            usage_collector.collect(ev.metrics)
            metrics.log_metrics(ev.metrics)
        
        @agent_session.on("error")
        def on_error(error: Exception):
            logger.log_error(error)
        
        await agent_session.start(agent=agent, room=ctx.room)
        logger.log_event("agent_started", {})
        
        await silence_monitor.start()
        
        # Greet the caller
        await agent_session.generate_reply(
            instructions="Поприветствуй пользователя кратко и спроси чем можешь помочь."
        )
        
        while not call_state["ending"]:
            await asyncio.sleep(1.0)
        
    except Exception as e:
        logger.log_error(e, context={"phase": "agent_session"})
        if agent_session:
            try:
                await agent_session.generate_reply(
                    instructions="Произошла техническая ошибка. Извинись и попроси перезвонить позже."
                )
                await asyncio.sleep(3.0)
            except Exception:
                pass
        raise
    finally:
        await silence_monitor.stop()
        logger.log_event("latency_summary", latency_metrics.get_summary())
        try:
            usage = usage_collector.get_summary()
            logger.log_event("usage_summary", {
                "llm_tokens": usage.llm_prompt_tokens + usage.llm_completion_tokens,
                "tts_chars": usage.tts_characters_count,
                "stt_audio_s": round(usage.stt_audio_duration, 2),
            })
        except Exception:
            pass
        logger.log_summary()


async def hangup_call():
    """End the call by deleting the room."""
    ctx = get_job_context()
    if ctx:
        await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))


if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)
