import asyncio
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli
from dotenv import load_dotenv

load_dotenv()


async def entrypoint(ctx: JobContext):
    """Test agent - just sends test messages"""

    await ctx.connect()
    print(f"✅ Connected to room: {ctx.room.name}")

    # Send a test message every 3 seconds
    for i in range(10):
        await asyncio.sleep(3)
        message = f"Test message #{i+1}"
        print(f"📤 Sending: {message}")

        await ctx.room.local_participant.publish_data(
            message.encode('utf-8'),
            topic='lk.transcription',
            reliable=True
        )
        print(f"✅ Sent!")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
