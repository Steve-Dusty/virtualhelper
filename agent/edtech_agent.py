import asyncio
from collections import deque
from datetime import datetime
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from dotenv import load_dotenv

load_dotenv()


class ConversationAnalyzer:
    """Analyzes classroom conversations and generates helpful insights"""

    def __init__(self, llm_model="gpt-4o-mini"):
        self.llm = openai.LLM(model=llm_model)
        self.transcript_buffer = deque(maxlen=50)  # Keep last 50 messages
        self.message_count = 0

    def add_message(self, speaker: str, text: str, role: str):
        """Add a transcription to the buffer"""
        self.transcript_buffer.append({
            'speaker': speaker,
            'text': text,
            'role': role,  # 'teacher' or 'student'
            'timestamp': datetime.now().isoformat()
        })
        self.message_count += 1

    def is_question(self, text: str) -> bool:
        """Detect if text contains a question"""
        question_indicators = ['?', 'what', 'why', 'how', 'when', 'where', 'who', 'can you', 'could you']
        text_lower = text.lower()
        return '?' in text or any(q in text_lower for q in question_indicators)

    async def generate_helper(self, context_messages: int = 10) -> str:
        """Generate AI helper based on recent conversation"""
        if len(self.transcript_buffer) < 3:
            return None

        # Get recent context
        recent = list(self.transcript_buffer)[-context_messages:]

        # Format conversation
        conversation = "\n".join([
            f"{msg['role'].upper()} ({msg['speaker']}): {msg['text']}"
            for msg in recent
        ])

        # Create prompt for AI helper
        prompt = f"""You are an AI teaching assistant helping students understand a live classroom discussion.

Recent conversation:
{conversation}

Based on this conversation, provide a helpful explanation that:
1. Summarizes the key teaching points
2. Explains complex concepts in simpler terms
3. Answers any student questions
4. Provides additional context if needed

Keep it concise (2-3 sentences) and student-friendly."""

        try:
            # Generate response
            stream = self.llm.chat(
                chat_ctx=agents.llm.ChatContext().append(
                    role="user",
                    text=prompt
                )
            )

            response = ""
            async for chunk in stream:
                response += chunk.choices[0].delta.content or ""

            return response.strip()
        except Exception as e:
            print(f"❌ Error generating helper: {e}")
            return None

    async def answer_question(self, question: str, asker_role: str) -> str:
        """Generate targeted answer to a student question"""
        # Get recent teaching context
        recent = list(self.transcript_buffer)[-15:]

        context = "\n".join([
            f"{msg['role'].upper()}: {msg['text']}"
            for msg in recent
        ])

        prompt = f"""You are an AI teaching assistant. A {asker_role} just asked:

"{question}"

Recent classroom context:
{context}

Provide a clear, helpful answer that:
1. Directly addresses the question
2. Builds on what the teacher has been explaining
3. Is appropriate for the student level
4. Is concise (2-3 sentences)"""

        try:
            stream = self.llm.chat(
                chat_ctx=agents.llm.ChatContext().append(
                    role="user",
                    text=prompt
                )
            )

            response = ""
            async for chunk in stream:
                response += chunk.choices[0].delta.content or ""

            return response.strip()
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            return None


async def entrypoint(ctx: JobContext):
    """EdTech AI agent for classroom assistance"""

    print("\n" + "="*80)
    print(f"🎓 EDTECH AI AGENT STARTING")
    print(f"📍 Room: {ctx.room.name}")
    print("="*80 + "\n")

    # Initialize STT with VAD
    stt = openai.STT()
    vad = silero.VAD.load()

    # Initialize conversation analyzer
    analyzer = ConversationAnalyzer()

    # Track active transcriptions
    active_transcriptions = {}

    async def transcribe_track(track: rtc.Track, participant: rtc.RemoteParticipant):
        """Transcribe a single audio track"""
        print(f"\n🎤 STARTING TRANSCRIPTION - {participant.identity}")

        # Determine role from participant identity or metadata
        role = "teacher" if "teacher" in participant.identity.lower() else "student"
        print(f"   Role: {role}")

        audio_stream = rtc.AudioStream(track)
        stream_adapter = agents.stt.StreamAdapter(stt=stt, vad=vad)
        stt_stream = stream_adapter.stream()

        async def process_transcription():
            """Process and publish transcriptions with AI analysis"""
            print(f"👂 Listening to {participant.identity}...")
            try:
                async for event in stt_stream:
                    if event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT and event.alternatives:
                        text = event.alternatives[0].text
                        if text.strip():
                            print(f"\n📝 [{role.upper()}] {participant.identity}: {text}")

                            # 1. Publish raw transcription
                            await ctx.room.local_participant.publish_data(
                                payload=text.encode('utf-8'),
                                topic='lk.transcription',
                                reliable=True
                            )

                            # 2. Add to analyzer
                            analyzer.add_message(participant.identity, text, role)

                            # 3. Check if student asked a question
                            is_question = analyzer.is_question(text)
                            if is_question and role == "student":
                                print(f"❓ Detected student question, generating answer...")
                                answer = await analyzer.answer_question(text, role)
                                if answer:
                                    print(f"🤖 AI Answer: {answer}")
                                    await ctx.room.local_participant.publish_data(
                                        payload=answer.encode('utf-8'),
                                        topic='lk.qa',  # Question-Answer topic
                                        reliable=True
                                    )

                            # 4. Generate helper every N messages
                            if analyzer.message_count % 5 == 0:  # Every 5 messages
                                print(f"🧠 Generating AI helper summary...")
                                helper = await analyzer.generate_helper()
                                if helper:
                                    print(f"💡 AI Helper: {helper}")
                                    await ctx.room.local_participant.publish_data(
                                        payload=helper.encode('utf-8'),
                                        topic='lk.helper',  # AI helper topic
                                        reliable=True
                                    )

            except Exception as e:
                print(f"❌ Error in transcription: {e}")
                import traceback
                traceback.print_exc()

        async def push_audio():
            """Push audio frames to STT"""
            frame_count = 0
            try:
                async for event in audio_stream:
                    stt_stream.push_frame(event.frame)
                    frame_count += 1
            except Exception as e:
                print(f"❌ Error pushing audio: {e}")
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
    print("🎓 EDTECH AI AGENT IS NOW ACTIVE")
    print("📝 Transcribing all speech")
    print("💡 Generating AI helpers every 5 messages")
    print("❓ Answering student questions automatically")
    print("="*80 + "\n")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
