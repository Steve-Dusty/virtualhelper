from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli
from dotenv import load_dotenv

load_dotenv()


async def entrypoint(ctx: JobContext):
    """Correct approach - uses AgentSession for automatic transcription"""

    print(f"🤖 Starting agent for room: {ctx.room.name}")

    # Connect with audio only
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print("✅ Connected to room")

    # Create agent session with STT - this automatically:
    # 1. Subscribes to participant audio
    # 2. Consumes audio frames
    # 3. Transcribes speech
    # 4. Publishes to 'lk.transcription' topic
    session = agents.llm.LLMContext()
    session = agents.llm.LLMAssistant(
        stt="deepgram/nova-2-general",  # Deepgram STT
        llm=None,  # No LLM needed for transcription only
        tts=None,  # No TTS needed
    )

    # Start the session - transcriptions happen automatically
    session.start(ctx.room)

    print("👂 Agent is transcribing all audio")
    print("📡 Transcriptions publishing to 'lk.transcription' topic")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
