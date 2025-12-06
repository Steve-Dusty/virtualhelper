import logging
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("transcription-agent")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    """Simple transcription agent using AgentSession"""

    logger.info(f"🤖 Agent starting for room: {ctx.room.name}")

    # Connect to room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    logger.info(f"✅ Connected to room: {ctx.room.name}")

    # Create agent session with STT
    # This automatically publishes transcriptions to 'lk.transcription' topic
    assistant = agents.llm.LLMAssistant(
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=openai.STT(),  # Speech-to-text
        tts=None,  # No text-to-speech needed for transcription-only
        vad=silero.VAD.load(),  # Voice activity detection
        chat_ctx=None,  # No chat context needed
    )

    # Start the assistant
    # Transcriptions will automatically be published to the room
    assistant.start(ctx.room)

    logger.info("👂 Agent is now transcribing all audio in the room")
    logger.info("📡 Transcriptions will be published to 'lk.transcription' topic")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
