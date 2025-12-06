import asyncio
import logging
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import deepgram
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("transcription-agent")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    """Simple transcription with Deepgram (actual streaming STT)"""

    print(f"🤖 Starting transcription agent for room: {ctx.room.name}")

    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ Connected to room")

    # Deepgram supports TRUE streaming (unlike OpenAI Whisper)
    stt = deepgram.STT(model="nova-2-general")

    active_tasks = {}

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"🎤 Audio track from {participant.identity}")

            async def transcribe():
                audio_stream = rtc.AudioStream(track)
                stt_stream = stt.stream()

                async def handle_transcription():
                    async for event in stt_stream:
                        if event.is_final and event.alternatives:
                            text = event.alternatives[0].text.strip()
                            if text:
                                print(f"📝 {participant.identity}: {text}")
                                await ctx.room.local_participant.publish_data(
                                    text.encode('utf-8'),
                                    topic='lk.transcription',
                                    reliable=True
                                )

                async def push_audio():
                    count = 0
                    async for frame in audio_stream:
                        stt_stream.push_frame(frame)
                        count += 1
                        if count == 1:
                            print("✅ Audio frames flowing")
                    await stt_stream.aclose()

                await asyncio.gather(push_audio(), handle_transcription())

            task = asyncio.create_task(transcribe())
            active_tasks[participant.identity] = task

    @ctx.room.on("track_unsubscribed")
    def on_track_unsubscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if participant.identity in active_tasks:
            active_tasks[participant.identity].cancel()
            del active_tasks[participant.identity]

    print("👂 Listening for audio...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
