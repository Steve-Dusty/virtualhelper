import asyncio
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()


async def entrypoint(ctx: JobContext):
    """Debug agent to see what's happening"""

    print("\n" + "="*80)
    print(f"🤖 DEBUG AGENT STARTED!!!")
    print(f"📍 Room: {ctx.room.name}")
    print(f"📍 Job: {ctx.job}")
    print("="*80 + "\n")

    # Setup event handlers BEFORE connecting
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        print(f"👤 PARTICIPANT CONNECTED: {participant.identity}")

    @ctx.room.on("track_published")
    def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        print(f"📢 TRACK PUBLISHED: {publication.kind} from {participant.identity}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        print(f"✅ TRACK SUBSCRIBED: {track.kind} from {participant.identity}")
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"🎤 AUDIO TRACK! Starting transcription...")
            asyncio.create_task(transcribe_audio(track, participant, ctx))

    # Connect to room
    print("🔌 Connecting to room...")
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ CONNECTED to room: {ctx.room.name}")

    # Check existing participants
    print(f"\n🔍 Current participants in room:")
    for p in ctx.room.remote_participants.values():
        print(f"  - {p.identity}")
        for pub in p.track_publications.values():
            print(f"    - Track: {pub.kind}, subscribed={pub.subscribed}")
            if pub.subscribed and pub.track and pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"      🎤 Found existing audio! Starting transcription...")
                asyncio.create_task(transcribe_audio(pub.track, p, ctx))

    print("\n👂 Agent is listening...\n")


async def transcribe_audio(track: rtc.Track, participant: rtc.RemoteParticipant, ctx: JobContext):
    """Transcribe audio from a track"""
    print(f"\n🎙️ TRANSCRIBE_AUDIO called for {participant.identity}")

    try:
        # Create STT
        stt = openai.STT()
        vad = silero.VAD.load()

        print(f"✅ STT and VAD loaded for {participant.identity}")

        # Create audio stream
        audio_stream = rtc.AudioStream(track)
        print(f"✅ Audio stream created for {participant.identity}")

        # Create STT stream with VAD
        stt_stream = agents.stt.StreamAdapter(stt=stt, vad=vad).stream()
        print(f"✅ STT stream created for {participant.identity}")

        frame_count = 0

        # Push audio frames
        async def push_frames():
            nonlocal frame_count
            async for event in audio_stream:
                stt_stream.push_frame(event.frame)  # Use event.frame, not event!
                frame_count += 1
                if frame_count % 50 == 0:
                    print(f"🎵 {frame_count} frames from {participant.identity}")

        # Process transcriptions
        async def process_events():
            async for event in stt_stream:
                print(f"🔔 STT EVENT type={event.type}")
                if event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT and event.alternatives:
                    text = event.alternatives[0].text
                    if text.strip():
                        print(f"\n✨ TRANSCRIPTION: {text}")
                        await ctx.room.local_participant.publish_data(
                            payload=text.encode('utf-8'),
                            topic='lk.transcription',
                            reliable=True
                        )
                        print(f"✅ Published!\n")

        await asyncio.gather(push_frames(), process_events())

    except Exception as e:
        print(f"❌ ERROR in transcribe_audio: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting debug agent worker...")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
