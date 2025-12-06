import asyncio
import logging
import os
from typing import Annotated
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, tokenize, tts
from livekit.plugins import openai, silero
from langchain_gradient import ChatGradient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("classroom-agent")
logger.setLevel(logging.INFO)


class ConversationAnalyzer:
    """Analyzes classroom conversation and provides summaries"""

    def __init__(self):
        self.transcript = []
        # Use DigitalOcean Gradient AI instead of OpenAI
        self.llm = ChatGradient(
            model="llama3.3-70b-instruct",
            api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
        )

    def add_transcript(self, speaker: str, text: str):
        """Add a new line to the transcript"""
        self.transcript.append(f"{speaker}: {text}")
        print(f"\n📝 TRANSCRIPTION: {speaker} said: {text}")
        logger.info(f"📝 {speaker}: {text}")

    async def get_summary(self) -> str:
        """Generate a summary of the conversation so far"""
        if not self.transcript:
            return "No conversation yet."

        full_transcript = "\n".join(self.transcript[-20:])  # Last 20 messages

        prompt = f"""You are analyzing a classroom conversation. Here's the recent transcript:

{full_transcript}

Provide a brief summary of:
1. Main topics discussed
2. Key points made
3. Any questions asked

Keep it concise (2-3 sentences)."""

        messages = [
            ("system", """You are an AI classroom assistant analyzing real-time educational conversations. Your role:

1. Identify the main educational topics and concepts being discussed
2. Track student questions and highlight areas where students need clarification
3. Note key teaching points and important explanations from the teacher
4. Detect if students seem confused or engaged based on their questions
5. Summarize in a way that's useful for both teachers and students

Keep summaries concise (2-3 sentences) and focus on:
- What topic is being taught
- Key questions students asked
- Main concepts explained

Be direct and educational in tone."""),
            ("human", prompt)
        ]

        # Use LangChain's invoke method
        response = await asyncio.to_thread(self.llm.invoke, messages)

        return response.content


async def entrypoint(ctx: JobContext):
    """Main agent entry point"""
    print("\n" + "="*80)
    print(f"🤖 AGENT STARTING - Room: {ctx.room.name}")
    print("="*80 + "\n")
    logger.info(f"🤖 Agent starting for room: {ctx.room.name}")

    # Initialize conversation analyzer
    analyzer = ConversationAnalyzer()
    print("✅ Conversation analyzer initialized")

    # Connect to the room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ Connected to room: {ctx.room.name}")
    print(f"✅ Auto-subscribing to AUDIO ONLY")
    logger.info("✅ Connected to room")

    # Initialize STT (Speech-to-Text) with OpenAI Whisper
    # Note: Whisper doesn't support streaming, so we use StreamAdapter with VAD
    stt = openai.STT()
    vad = silero.VAD.load()  # Voice Activity Detection

    # Track active transcriptions
    active_transcriptions = {}

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle new audio tracks (when someone speaks)"""
        print(f"\n🔔 NEW TRACK SUBSCRIBED - Type: {track.kind}, Participant: {participant.identity}")
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"🎤 AUDIO TRACK DETECTED - Starting transcription for {participant.identity}")
            logger.info(f"🎤 Subscribed to {participant.identity}'s audio")

            # Start transcribing this participant's audio
            async def transcribe():
                print(f"🎙️  Starting AudioStream for {participant.identity}")
                audio_stream = rtc.AudioStream(track)

                # Use StreamAdapter with VAD for non-streaming STT
                stream_adapter = agents.stt.StreamAdapter(
                    stt=stt,
                    vad=vad
                )
                stt_stream = stream_adapter.stream()
                print(f"🎙️  STT stream created with VAD for {participant.identity}")

                async def process_stt():
                    """Process STT results"""
                    print(f"👂 Waiting for STT events from {participant.identity}...")
                    try:
                        async for event in stt_stream:
                            print(f"🔊 Got STT event: is_final={event.is_final}, text='{event.alternatives[0].text if event.alternatives else 'N/A'}'")
                            if event.is_final:
                                text = event.alternatives[0].text
                                if text.strip():
                                    analyzer.add_transcript(participant.identity, text)

                                    # Every 10 messages, generate a summary
                                    if len(analyzer.transcript) % 10 == 0:
                                        print("\n" + "="*80)
                                        print("🧠 GENERATING AI SUMMARY...")
                                        summary = await analyzer.get_summary()
                                        print(f"\n📊 AI SUMMARY FROM GRADIENT:\n{summary}")
                                        print("="*80 + "\n")
                                        logger.info(f"📊 SUMMARY: {summary}")

                                        # Publish summary to the room
                                        await ctx.room.local_participant.publish_data(
                                            payload=summary.encode('utf-8'),
                                            topic="summary",
                                            reliable=True
                                        )
                                        print("📤 Summary published to room")
                                        logger.info("📤 Summary published to room")
                    except Exception as e:
                        print(f"❌ Error in STT processing for {participant.identity}: {e}")
                        logger.error(f"STT error: {e}")

                # Push audio to STT
                async def push_audio():
                    print(f"🎵 Starting to push audio frames for {participant.identity}")
                    frame_count = 0
                    async for frame in audio_stream:
                        stt_stream.push_frame(frame)
                        frame_count += 1
                        if frame_count % 50 == 0:  # Log more frequently
                            print(f"📊 Pushed {frame_count} audio frames for {participant.identity}")
                    print(f"🛑 Audio stream ended for {participant.identity}, flushing...")
                    await stt_stream.flush()

                await asyncio.gather(push_audio(), process_stt())

            # Store and start transcription task
            task = asyncio.create_task(transcribe())
            active_transcriptions[participant.identity] = task

    @ctx.room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle when someone stops sharing audio"""
        if participant.identity in active_transcriptions:
            active_transcriptions[participant.identity].cancel()
            del active_transcriptions[participant.identity]
            logger.info(f"🔇 Unsubscribed from {participant.identity}'s audio")

    print("\n" + "="*80)
    print("👂 AGENT IS NOW LISTENING TO THE CLASSROOM")
    print(f"📡 Waiting for participants to join room: {ctx.room.name}")
    print("="*80 + "\n")
    logger.info("👂 Agent is listening to the classroom...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
