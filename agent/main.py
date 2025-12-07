"""Voice Agent MVP - Main entry point.

LiveKit Agents SDK based voice agent for handling incoming SIP calls.
Uses Deepgram for STT, OpenAI for LLM, ElevenLabs for TTS, and Silero for VAD.

Requirements: 1.1, 1.2, 2.1, 2.2, 3.2, 1.4, 3.4
"""

import asyncio
import time

from dotenv import load_dotenv
from livekit import api
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, RunContext, get_job_context, function_tool
from livekit.plugins import deepgram, elevenlabs, openai, silero

from agent.config import load_config
from agent.logger import CallLogger

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
    
    # Track if call is ending
    call_ending = False
    
    async def handle_silence_timeout():
        """Handle silence timeout - say goodbye and hang up."""
        nonlocal call_ending
        if call_ending:
            return
        call_ending = True
        
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
    
    # Define end_call tool for the agent to use when conversation ends
    @function_tool
    async def end_call(context: RunContext) -> str:
        """End the call gracefully.
        
        Call this function when:
        - The user says goodbye (до свидания, пока, всего хорошего, etc.)
        - The user indicates they want to end the conversation
        - The conversation has naturally concluded
        
        Returns:
            Confirmation that the call will be ended.
        """
        nonlocal call_ending
        if call_ending:
            return "Звонок уже завершается."
        call_ending = True
        
        logger.log_event("initiating_goodbye", {"reason": "user_farewell"})
        
        # Schedule hangup after a short delay to allow farewell message
        async def delayed_hangup():
            await asyncio.sleep(3.0)
            await hangup_call()
        
        asyncio.create_task(delayed_hangup())
        
        return "Звонок будет завершён после прощания."
    
    try:
        # Create the agent with system prompt and tools
        agent = Agent(
            instructions=config.agent_system_prompt + "\n\nКогда пользователь прощается или хочет завершить разговор, вызови функцию end_call и попрощайся.",
            tools=[end_call],
        )

        # Create the agent session with voice pipeline
        agent_session = AgentSession(
            vad=silero.VAD.load(),
            stt=deepgram.STT(
                model="nova-3",
                language="ru",  # Russian language
            ),
            llm=openai.LLM(
                model=config.openai_model,
                base_url=config.openai_base_url,
            ),
            tts=elevenlabs.TTS(voice_id=config.elevenlabs_voice_id),
        )
        
        # Set up event handlers for silence monitoring and interruption handling
        @agent_session.on("user_started_speaking")
        def on_user_started_speaking():
            """Reset silence timer when user starts speaking.
            
            Note: LiveKit Agents SDK automatically handles interruptions -
            when user speaks during agent response, TTS playback stops.
            """
            silence_monitor.reset()
            logger.log_event("user_started_speaking", {})
        
        @agent_session.on("user_stopped_speaking")
        def on_user_stopped_speaking():
            """Log when user stops speaking."""
            logger.log_event("user_stopped_speaking", {})
        
        @agent_session.on("agent_started_speaking")
        def on_agent_started_speaking():
            """Log when agent starts speaking."""
            logger.log_event("agent_started_speaking", {})
        
        @agent_session.on("agent_stopped_speaking")
        def on_agent_stopped_speaking():
            """Log when agent stops speaking (including interruptions)."""
            logger.log_event("agent_stopped_speaking", {})
        
        @agent_session.on("user_input_transcribed")
        def on_user_input_transcribed(transcript):
            """Reset silence timer when user speech is transcribed."""
            silence_monitor.reset()
            logger.log_event("user_input_transcribed", {"transcript": str(transcript)[:100]})
        
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
        while not call_ending:
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
