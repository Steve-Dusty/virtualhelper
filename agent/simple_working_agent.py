import asyncio
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, tokenize, tts
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()


async def entrypoint(ctx: JobContext):
    """Simple voice pipeline agent for transcription"""

    print("\n" + "="*80)
    print(f"🤖 SIMPLE TRANSCRIPTION AGENT STARTING")
    print(f"📍 Room: {ctx.room.name}")
    print("="*80 + "\n")

    # Connect to the room first
    await ctx.connect()
    print(f"✅ Connected to room: {ctx.room.name}")

    # Create a simple pipeline agent with STT
    assistant = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),  # Minimal LLM just for pipeline
        tts=openai.TTS(),  # Minimal TTS
    )

    # Listen for transcription events
    @assistant.on("user_speech_committed")
    def on_user_speech_committed(msg: agents.llm.ChatMessage):
        """When user speech is finalized"""
        print(f"\n📝 USER SPEECH: {msg.content}")

        # Publish transcription to room
        asyncio.create_task(
            ctx.room.local_participant.publish_data(
                payload=msg.content.encode('utf-8'),
                topic='lk.transcription',
                reliable=True
            )
        )
        print(f"✅ Published transcription\n")

    # Start the assistant
    assistant.start(ctx.room)
    print("✅ Assistant started and listening")

    # Keep running
    await asyncio.sleep(float('inf'))


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
