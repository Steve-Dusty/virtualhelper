import asyncio
import json
from collections import deque
from datetime import datetime
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, silero
from gradient import Gradient
from dotenv import load_dotenv
import os

load_dotenv()


class SmartDashboardAnalyzer:
    """Pre-computes summaries every 5 seconds for instant dashboard responses"""

    def __init__(self, model="llama3.3-70b-instruct"):
        self.gradient_client = Gradient(
            model_access_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY")
        )
        self.model = model
        self.transcript_buffer = deque(maxlen=100)  # Keep more for better analysis

        # Cache for pre-computed summaries
        self.cache = {
            'summary': None,
            'topics': [],
            'in_depth': None,
            'last_updated': None
        }

        self.message_count = 0

    def add_message(self, speaker: str, text: str, role: str):
        """Add a transcription to the buffer"""
        self.transcript_buffer.append({
            'speaker': speaker,
            'text': text,
            'role': role,
            'timestamp': datetime.now().isoformat()
        })
        self.message_count += 1

    def get_conversation_text(self, last_n: int = None):
        """Get formatted conversation text"""
        messages = list(self.transcript_buffer) if not last_n else list(self.transcript_buffer)[-last_n:]
        return "\n".join([
            f"{msg['role'].upper()} ({msg['speaker']}): {msg['text']}"
            for msg in messages
        ])

    def is_question(self, text: str) -> bool:
        """Detect if text contains a question"""
        question_indicators = ['?', 'what', 'why', 'how', 'when', 'where', 'who', 'can you', 'could you']
        text_lower = text.lower()
        return '?' in text or any(q in text_lower for q in question_indicators)

    async def precompute_all(self):
        """Pre-compute all dashboard data (runs every 5 seconds)"""
        if len(self.transcript_buffer) < 3:
            return None

        print(f"\n🔄 Pre-computing dashboard data...")

        conversation = self.get_conversation_text(last_n=30)

        # Single efficient API call with all questions
        combined_prompt = f"""You are analyzing a live classroom conversation. Based on this recent discussion:

{conversation}

Provide a JSON response with:
1. "summary": A 2-3 sentence summary of what's being taught
2. "topics": A list of 3-5 key topics/concepts discussed (just topic names)
3. "in_depth": A detailed explanation (4-5 sentences) that helps students understand the main concepts better

Format as valid JSON:
{{"summary": "...", "topics": ["topic1", "topic2", ...], "in_depth": "..."}}"""

        try:
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[
                    {"role": "user", "content": combined_prompt}
                ],
                model=self.model,
                max_tokens=300,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()

                # Try to parse JSON
                try:
                    # Extract JSON if it's wrapped in markdown
                    if '```json' in content:
                        content = content.split('```json')[1].split('```')[0].strip()
                    elif '```' in content:
                        content = content.split('```')[1].split('```')[0].strip()

                    data = json.loads(content)

                    self.cache = {
                        'summary': data.get('summary', 'Analyzing conversation...'),
                        'topics': data.get('topics', []),
                        'in_depth': data.get('in_depth', ''),
                        'last_updated': datetime.now().isoformat()
                    }

                    print(f"✅ Dashboard data cached:")
                    print(f"   📊 Summary: {self.cache['summary'][:60]}...")
                    print(f"   📚 Topics: {', '.join(self.cache['topics'][:3])}...")

                    return self.cache

                except json.JSONDecodeError:
                    # Fallback: parse manually
                    print(f"⚠️ JSON parse failed, using text fallback")
                    self.cache = {
                        'summary': content[:200],
                        'topics': ['Main topic'],
                        'in_depth': content,
                        'last_updated': datetime.now().isoformat()
                    }
                    return self.cache

        except Exception as e:
            print(f"❌ Error pre-computing: {e}")
            import traceback
            traceback.print_exc()

        return None

    async def answer_student_question(self, question: str) -> str:
        """Generate answer when student asks a question"""
        context = self.get_conversation_text(last_n=20)

        prompt = f"""You are an AI teaching assistant. A student just asked: "{question}"

Recent classroom discussion:
{context}

Current summary: {self.cache.get('summary', 'N/A')}

Provide a clear, helpful answer (2-3 sentences) that:
1. Directly answers the question
2. Relates to what the teacher is teaching
3. Is easy to understand

Answer:"""

        try:
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=150,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Error answering: {e}")

        return None


async def entrypoint(ctx: JobContext):
    """Smart Dashboard Agent with pre-computed summaries"""

    print("\n" + "="*80)
    print(f"🎯 SMART DASHBOARD AGENT")
    print(f"📍 Room: {ctx.room.name}")
    print(f"🤖 AI: llama3.3-70b-instruct")
    print(f"⚡ Pre-computes summaries every 5 seconds for instant results!")
    print("="*80 + "\n")

    # Initialize STT with VAD
    print("🎤 Initializing OpenAI STT...")
    stt = openai.STT()
    vad = silero.VAD.load()

    # Initialize smart analyzer
    print("🧠 Initializing Smart Analyzer...")
    analyzer = SmartDashboardAnalyzer()

    # Track active transcriptions
    active_transcriptions = {}

    # Background task for pre-computing summaries
    async def precompute_task():
        """Background task that pre-computes summaries every 5 seconds"""
        await asyncio.sleep(10)  # Wait 10 seconds for initial data

        while True:
            try:
                cache_data = await analyzer.precompute_all()

                if cache_data:
                    # Publish cache to frontend
                    payload = json.dumps(cache_data).encode('utf-8')
                    await ctx.room.local_participant.publish_data(
                        payload=payload,
                        topic='lk.dashboard-cache',
                        reliable=True
                    )
                    print(f"📤 Published dashboard cache to frontend\n")

            except Exception as e:
                print(f"❌ Error in precompute task: {e}")

            await asyncio.sleep(5)  # Every 5 seconds

    async def transcribe_track(track: rtc.Track, participant: rtc.RemoteParticipant):
        """Transcribe audio track"""
        print(f"\n🎤 STARTING TRANSCRIPTION - {participant.identity}")

        role = "teacher" if "teacher" in participant.identity.lower() else "student"
        print(f"   Role: {role}")

        audio_stream = rtc.AudioStream(track)
        stream_adapter = agents.stt.StreamAdapter(stt=stt, vad=vad)
        stt_stream = stream_adapter.stream()

        async def process_transcription():
            """Process transcriptions"""
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

                            # 3. If STUDENT asks question → answer immediately
                            if analyzer.is_question(text) and role == "student":
                                print(f"❓ Student question detected!")
                                answer = await analyzer.answer_student_question(text)
                                if answer:
                                    print(f"🤖 Answer: {answer}\n")

                                    # Send answer with question context
                                    qa_data = json.dumps({
                                        'question': text,
                                        'answer': answer,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    await ctx.room.local_participant.publish_data(
                                        payload=qa_data.encode('utf-8'),
                                        topic='lk.student-qa',
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
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"\n🎤 AUDIO TRACK DETECTED - {participant.identity}")
            task = asyncio.create_task(transcribe_track(track, participant))
            active_transcriptions[participant.identity] = task

    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if participant.identity in active_transcriptions:
            active_transcriptions[participant.identity].cancel()
            del active_transcriptions[participant.identity]

    # Register event handlers BEFORE connecting
    ctx.room.on("track_subscribed", on_track_subscribed)
    ctx.room.on("track_unsubscribed", on_track_unsubscribed)

    # Connect to the room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ Connected to room: {ctx.room.name}")

    # Handle existing participants
    print(f"\n🔍 Checking for existing participants...")
    for participant in ctx.room.remote_participants.values():
        print(f"  - Found participant: {participant.identity}")
        for track_pub in participant.track_publications.values():
            if track_pub.subscribed and track_pub.track and track_pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"    🎤 Already has audio track, starting transcription...")
                task = asyncio.create_task(transcribe_track(track_pub.track, participant))
                active_transcriptions[participant.identity] = task

    # Start background pre-compute task
    print("\n🚀 Starting background pre-compute task (every 5 seconds)...")
    asyncio.create_task(precompute_task())

    print("\n" + "="*80)
    print("🎯 SMART DASHBOARD AGENT IS NOW ACTIVE")
    print("🎤 Transcription: OpenAI Whisper")
    print("🧠 AI Analysis: Gradient (llama3.3-70b-instruct)")
    print("⚡ Pre-computing summaries every 5 seconds")
    print("❓ Instant answers when students ask questions")
    print("="*80 + "\n")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
