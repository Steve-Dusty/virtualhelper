import asyncio
import logging
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("transcription-agent")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    """Pure transcription agent - transcribes all audio and sends to frontend"""

    print("\n" + "="*80)
    print(f"🤖 TRANSCRIPTION AGENT STARTING - Room: {ctx.room.name}")
    print(f"📍 Job ID: {ctx.job.id if ctx.job else 'N/A'}")
    print(f"📍 Agent ID: {ctx.job.agent_name if ctx.job else 'N/A'}")
    print("="*80 + "\n")

    # Initialize STT with VAD
    stt = openai.STT()
    vad = silero.VAD.load()

    # Track active transcriptions
    active_transcriptions = {}

    async def transcribe_track(track: rtc.Track, participant: rtc.RemoteParticipant):
        """Transcribe a single audio track"""
        print(f"\n🎤 STARTING TRANSCRIPTION - {participant.identity}")

        # Create audio stream and STT stream with VAD
        audio_stream = rtc.AudioStream(track)

        # Use StreamAdapter to combine STT with VAD
        stream_adapter = agents.stt.StreamAdapter(
            stt=stt,
            vad=vad,
        )
        stt_stream = stream_adapter.stream()
        print(f"🎙️  STT stream with VAD created for {participant.identity}")

        async def process_transcription():
            """Process and publish transcriptions"""
            print(f"👂 Listening to {participant.identity}...")
            try:
                async for event in stt_stream:
                    print(f"🔔 Got STT event type={event.type}")

                    # Only process final transcriptions
                    if event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT and event.alternatives:
                        text = event.alternatives[0].text
                        if text.strip():
                            print(f"\n📝 TRANSCRIPTION from {participant.identity}: {text}")

                            # Publish to 'lk.transcription' topic (official LiveKit topic)
                            await ctx.room.local_participant.publish_data(
                                payload=text.encode('utf-8'),
                                topic='lk.transcription',
                                reliable=True
                            )
                            print(f"✅ Published transcription to room\n")
            except Exception as e:
                print(f"❌ Error in transcription: {e}")
                import traceback
                traceback.print_exc()

        async def push_audio():
            """Push audio frames to STT"""
            frame_count = 0
            try:
                async for event in audio_stream:
                    stt_stream.push_frame(event.frame)  # Use event.frame, not event!
                    frame_count += 1
                    if frame_count % 100 == 0:
                        print(f"🎵 Pushed {frame_count} audio frames for {participant.identity}")
                print(f"🛑 Audio stream ended, total frames: {frame_count}")
            except Exception as e:
                print(f"❌ Error pushing audio: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await stt_stream.aclose()

        await asyncio.gather(push_audio(), process_transcription())

    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle new audio tracks"""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"\n🎤 AUDIO TRACK DETECTED - {participant.identity}")
            # Start transcription task
            task = asyncio.create_task(transcribe_track(track, participant))
            active_transcriptions[participant.identity] = task

    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Cleanup when audio stops"""
        if participant.identity in active_transcriptions:
            active_transcriptions[participant.identity].cancel()
            del active_transcriptions[participant.identity]
            print(f"🔇 Stopped transcribing {participant.identity}")

    # Register event handlers BEFORE connecting
    ctx.room.on("track_subscribed", on_track_subscribed)
    ctx.room.on("track_unsubscribed", on_track_unsubscribed)

    # Connect to the room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ Connected to room: {ctx.room.name}")
    print(f"✅ Auto-subscribing to AUDIO ONLY")

    # Handle existing participants with audio tracks
    print(f"\n🔍 Checking for existing participants...")
    for participant in ctx.room.remote_participants.values():
        print(f"  - Found participant: {participant.identity}")
        for track_pub in participant.track_publications.values():
            if track_pub.subscribed and track_pub.track and track_pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"    🎤 Already has audio track, starting transcription...")
                task = asyncio.create_task(transcribe_track(track_pub.track, participant))
                active_transcriptions[participant.identity] = task

    print("\n" + "="*80)
    print("👂 TRANSCRIPTION AGENT IS NOW LISTENING")
    print(f"📡 Transcriptions will be sent to topic: 'lk.transcription'")
    print("="*80 + "\n")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
