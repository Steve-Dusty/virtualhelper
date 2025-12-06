import asyncio
from collections import deque
from datetime import datetime
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from gradient import Gradient
from dotenv import load_dotenv
import os

load_dotenv()


class GradientAnalyzer:
    """Analyzes classroom conversations using DigitalOcean Gradient AI"""

    def __init__(self, model="llama3.3-70b-instruct"):
        # Initialize Gradient client
        self.gradient_client = Gradient(
            model_access_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY")
        )
        self.model = model
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
        print(f"📊 Buffer size: {len(self.transcript_buffer)} messages")

    def is_question(self, text: str) -> bool:
        """Detect if text contains a question"""
        question_indicators = ['?', 'what', 'why', 'how', 'when', 'where', 'who', 'can you', 'could you']
        text_lower = text.lower()
        return '?' in text or any(q in text_lower for q in question_indicators)

    async def generate_helper(self, context_messages: int = 10) -> str:
        """Generate AI helper based on recent conversation using Gradient"""
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
        system_prompt = """You are an AI teaching assistant helping students understand a live classroom discussion.

Based on the conversation, provide a helpful explanation that:
1. Summarizes the key teaching points
2. Explains complex concepts in simpler terms
3. Answers any student questions
4. Provides additional context if needed

Keep it concise (2-3 sentences) and student-friendly."""

        user_prompt = f"""Recent classroom conversation:
{conversation}

Provide a helpful summary/explanation:"""

        try:
            print(f"🧠 Calling Gradient AI ({self.model})...")

            # Call Gradient API
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                max_tokens=150,
                temperature=0.7
            )

            # Debug: print full response
            print(f"📊 Response object: {response}")
            print(f"📊 Choices: {response.choices}")

            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"📊 Content type: {type(content)}, value: {content}")

                if content:
                    result = content.strip()
                    print(f"✅ Generated helper: {result[:100]}...")
                    return result
                else:
                    print("⚠️ Content is None, trying without system message...")
                    # Retry without system message
                    response2 = await asyncio.to_thread(
                        self.gradient_client.chat.completions.create,
                        messages=[
                            {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                        ],
                        model=self.model,
                        max_tokens=150,
                        temperature=0.7
                    )
                    content2 = response2.choices[0].message.content
                    if content2:
                        result = content2.strip()
                        print(f"✅ Generated helper (retry): {result[:100]}...")
                        return result

            print("❌ No valid response from Gradient")
            return None

        except Exception as e:
            print(f"❌ Error generating helper: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def answer_question(self, question: str, asker_role: str) -> str:
        """Generate targeted answer to a student question using Gradient"""
        # Get recent teaching context
        recent = list(self.transcript_buffer)[-15:]

        context = "\n".join([
            f"{msg['role'].upper()}: {msg['text']}"
            for msg in recent
        ])

        system_prompt = """You are an AI teaching assistant in a live classroom. Answer student questions clearly and helpfully based on the recent discussion context."""

        user_prompt = f"""Recent classroom context:
{context}

A {asker_role} just asked: "{question}"

Provide a clear, helpful answer that:
1. Directly addresses the question
2. Builds on what the teacher has been explaining
3. Is appropriate for the student level
4. Is concise (2-3 sentences)

Answer:"""

        try:
            print(f"❓ Answering question with Gradient AI...")

            # Call Gradient API
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[
                    {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}  # Single user message
                ],
                model=self.model,
                max_tokens=120,
                temperature=0.7
            )

            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    result = content.strip()
                    print(f"✅ Generated answer: {result[:100]}...")
                    return result

            print("❌ No valid answer from Gradient")
            return None

        except Exception as e:
            print(f"❌ Error answering question: {e}")
            import traceback
            traceback.print_exc()
            return None


async def entrypoint(ctx: JobContext):
    """EdTech AI agent using DigitalOcean Gradient for analysis"""

    print("\n" + "="*80)
    print(f"🎓 EDTECH AI AGENT (Gradient-Powered)")
    print(f"📍 Room: {ctx.room.name}")
    print(f"🤖 AI Model: llama3.3-70b-instruct (DigitalOcean Gradient)")
    print("="*80 + "\n")

    # Initialize STT with VAD (still using OpenAI for transcription)
    print("🎤 Initializing OpenAI STT for transcription...")
    stt = openai.STT()
    vad = silero.VAD.load()

    # Initialize Gradient analyzer for AI
    print("🧠 Initializing Gradient AI for analysis...")
    analyzer = GradientAnalyzer()

    # Track active transcriptions
    active_transcriptions = {}

    async def transcribe_track(track: rtc.Track, participant: rtc.RemoteParticipant):
        """Transcribe a single audio track"""
        print(f"\n🎤 STARTING TRANSCRIPTION - {participant.identity}")

        # Determine role from participant identity
        role = "teacher" if "teacher" in participant.identity.lower() else "student"
        print(f"   Role: {role}")

        audio_stream = rtc.AudioStream(track)
        stream_adapter = agents.stt.StreamAdapter(stt=stt, vad=vad)
        stt_stream = stream_adapter.stream()

        async def process_transcription():
            """Process and publish transcriptions with Gradient AI analysis"""
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
                                print(f"❓ Detected student question!")
                                answer = await analyzer.answer_question(text, role)
                                if answer:
                                    print(f"🤖 AI Answer: {answer}\n")
                                    await ctx.room.local_participant.publish_data(
                                        payload=answer.encode('utf-8'),
                                        topic='lk.qa',
                                        reliable=True
                                    )

                            # 4. Generate helper every N messages
                            if analyzer.message_count % 5 == 0:  # Every 5 messages
                                print(f"💡 Generating AI helper summary...")
                                helper = await analyzer.generate_helper()
                                if helper:
                                    print(f"💡 AI Helper: {helper}\n")
                                    await ctx.room.local_participant.publish_data(
                                        payload=helper.encode('utf-8'),
                                        topic='lk.helper',
                                        reliable=True
                                    )

            except Exception as e:
                print(f"❌ Error in transcription: {e}")
                import traceback
                traceback.print_exc()

        async def push_audio():
            """Push audio frames to STT"""
            try:
                async for event in audio_stream:
                    stt_stream.push_frame(event.frame)
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
    print("🎤 Transcription: OpenAI Whisper")
    print("🧠 AI Analysis: DigitalOcean Gradient (llama3.3-70b-instruct)")
    print("💡 Generates helpers every 5 messages")
    print("❓ Answers student questions automatically")
    print("="*80 + "\n")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
