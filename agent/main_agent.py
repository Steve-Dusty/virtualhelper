"""
MAIN ORCHESTRATOR AGENT
This is the ONLY agent you need to run. It handles everything:
- Real-time transcription (OpenAI Whisper + Silero VAD)
- Pre-computed dashboard summaries (every 5 seconds)
- Student Q&A (automatic answers when questions detected)
- DigitalOcean Gradient AI for analysis (Llama 3.3 70B)
"""

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
import subprocess
import tempfile
import uuid
import re
from pathlib import Path

load_dotenv()


class CentralOrchestrator:
    """Centralized orchestrator for all AI classroom features"""

    def __init__(self, model="llama3.3-70b-instruct"):
        self.gradient_client = Gradient(
            model_access_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY")
        )
        self.model = model
        self.transcript_buffer = deque(maxlen=100)

        # Cache for dashboard
        self.cache = {
            'summary': None,
            'topics': [],
            'in_depth': None,
            'last_updated': None
        }

        self.message_count = 0

        # Animation tracking
        self.animation_files = {}  # Track: {request_id: {script_path, video_path, timestamp}}
        self.manim_timeout = 60  # seconds

    def add_message(self, speaker: str, text: str, role: str):
        """Add transcription to buffer"""
        self.transcript_buffer.append({
            'speaker': speaker,
            'text': text,
            'role': role,
            'timestamp': datetime.now().isoformat()
        })
        self.message_count += 1

    def get_conversation_text(self, last_n: int = None):
        """Get formatted conversation"""
        messages = list(self.transcript_buffer) if not last_n else list(self.transcript_buffer)[-last_n:]
        return "\n".join([
            f"{msg['role'].upper()} ({msg['speaker']}): {msg['text']}"
            for msg in messages
        ])

    def is_question(self, text: str) -> bool:
        """Detect questions"""
        question_indicators = ['?', 'what', 'why', 'how', 'when', 'where', 'who', 'can you', 'could you']
        text_lower = text.lower()
        return '?' in text or any(q in text_lower for q in question_indicators)

    async def precompute_dashboard(self):
        """Pre-compute all dashboard data (runs every 5 seconds)"""
        if len(self.transcript_buffer) < 3:
            return None

        print(f"\n🔄 Pre-computing dashboard data...")
        conversation = self.get_conversation_text(last_n=30)

        prompt = f"""Analyze this classroom conversation and provide a JSON response:

{conversation}

Return JSON with:
{{"summary": "2-3 sentence summary of what's being taught", "topics": ["topic1", "topic2", "topic3"], "in_depth": "4-5 sentence detailed explanation for students"}}"""

        try:
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=300,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()

                # Parse JSON
                try:
                    if '```json' in content:
                        content = content.split('```json')[1].split('```')[0].strip()
                    elif '```' in content:
                        content = content.split('```')[1].split('```')[0].strip()

                    data = json.loads(content)
                    self.cache = {
                        'summary': data.get('summary', 'Analyzing...'),
                        'topics': data.get('topics', []),
                        'in_depth': data.get('in_depth', ''),
                        'last_updated': datetime.now().isoformat()
                    }

                    print(f"✅ Cached: {self.cache['summary'][:50]}...")
                    return self.cache

                except json.JSONDecodeError:
                    # Fallback
                    self.cache = {
                        'summary': content[:200],
                        'topics': ['Discussion topic'],
                        'in_depth': content,
                        'last_updated': datetime.now().isoformat()
                    }
                    return self.cache

        except Exception as e:
            print(f"❌ Error pre-computing: {e}")

        return None

    async def answer_question(self, question: str) -> str:
        """Answer student question"""
        context = self.get_conversation_text(last_n=20)

        prompt = f"""A student asked: "{question}"

Recent discussion:
{context}

Provide a clear 2-3 sentence answer that directly addresses the question and relates to what's being taught.

Answer:"""

        try:
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=150,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Error answering: {e}")

        return None

    async def generate_manim_animation(self, question: str, request_id: str) -> dict:
        """
        Generate Manim animation code and execute it.
        Returns: {success: bool, video_id: str, error: str}
        """
        print(f"\n🎬 Generating Manim animation for: {question}")

        # 1. Get conversation context
        context = self.get_conversation_text(last_n=20)

        # 2. Generate Manim code using Gradient AI
        prompt = f"""You are a Manim expert creating educational animations.

Student Question: "{question}"

Classroom Context:
{context}

Generate a complete, working Manim script that:
1. Explains the concept visually
2. Uses simple animations (Text, Circle, Square, Arrow, MathTex)
3. Runs in 10-15 seconds
4. Is safe (no imports besides manim, no file I/O, no network)
5. Has a class named 'ExplainScene' that inherits from Scene

CRITICAL RULES:
- ONLY import from manim
- NO file operations (open, read, write)
- NO external libraries
- NO infinite loops
- Use self.play() for animations
- Use self.wait() between animations

Return ONLY the Python code, no explanations:

```python
from manim import *

class ExplainScene(Scene):
    def construct(self):
        # Your animation here
```
"""

        try:
            # Generate code
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=800,
                temperature=0.3  # Lower temperature for reliable code
            )

            if not response.choices or not response.choices[0].message.content:
                return {"success": False, "error": "No code generated"}

            code = response.choices[0].message.content.strip()

            # Extract code from markdown if wrapped
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0].strip()
            elif '```' in code:
                code = code.split('```')[1].split('```')[0].strip()

            # 3. Security validation
            if not self._validate_manim_code(code):
                return {"success": False, "error": "Generated code failed security validation"}

            # 4. Save to temporary file
            script_path = f"/tmp/manim_{request_id}.py"
            video_path = f"/tmp/output_{request_id}.mp4"

            with open(script_path, 'w') as f:
                f.write(code)

            print(f"✅ Code saved to {script_path}")

            # 5. Execute Manim
            print(f"🎬 Running Manim...")
            result = await asyncio.to_thread(
                self._run_manim,
                script_path,
                video_path,
                request_id
            )

            if result['success']:
                # Track file for cleanup
                self.animation_files[request_id] = {
                    'script_path': script_path,
                    'video_path': video_path,
                    'timestamp': datetime.now()
                }
                print(f"✅ Animation generated: {video_path}")
                return {
                    "success": True,
                    "video_id": request_id,
                    "duration": result.get('duration', 0)
                }
            else:
                # Cleanup on failure
                Path(script_path).unlink(missing_ok=True)
                return {"success": False, "error": result['error']}

        except Exception as e:
            print(f"❌ Animation generation error: {e}")
            return {"success": False, "error": str(e)}

    def _validate_manim_code(self, code: str) -> bool:
        """
        Security validation for generated Manim code.
        Returns False if code contains dangerous patterns.
        """
        dangerous_patterns = [
            r'import\s+(?!manim)',  # Only allow manim imports
            r'from\s+(?!manim)',    # Only allow from manim
            r'\bopen\b',            # File operations
            r'\beval\b',            # Code execution
            r'\bexec\b',            # Code execution
            r'\b__import__\b',      # Dynamic imports
            r'\bsubprocess\b',      # System calls
            r'\bos\.',              # OS operations
            r'\bsys\.',             # System operations
            r'requests\.',          # Network
            r'urllib\.',            # Network
            r'socket\.',            # Network
            r'while\s+True:',       # Infinite loops
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                print(f"❌ Security violation: {pattern}")
                return False

        # Must contain required class
        if 'class ExplainScene(Scene):' not in code:
            print(f"❌ Missing required class: ExplainScene")
            return False

        return True

    def _run_manim(self, script_path: str, output_path: str, request_id: str) -> dict:
        """
        Execute Manim script with timeout and error handling.
        """
        try:
            # Manim command: medium quality, output to specific location
            cmd = [
                'manim',
                '-qm',  # Medium quality (faster)
                '--format=mp4',
                '--media_dir=/tmp',
                f'--output_file=output_{request_id}.mp4',
                script_path,
                'ExplainScene'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.manim_timeout,
                cwd='/tmp'
            )

            if result.returncode == 0:
                # Manim creates nested directories, find the actual file
                media_path = Path(f"/tmp/videos/manim_{request_id}/480p15")
                video_file = media_path / f"output_{request_id}.mp4"

                if video_file.exists():
                    # Move to expected location
                    import shutil
                    shutil.move(str(video_file), output_path)
                    return {"success": True}
                else:
                    return {"success": False, "error": "Video file not found after rendering"}
            else:
                error_msg = result.stderr[:200]  # Truncate error
                print(f"❌ Manim error: {error_msg}")
                return {"success": False, "error": f"Manim rendering failed: {error_msg}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Animation generation timed out (60s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cleanup_old_animations(self):
        """
        Delete animation files older than 1 hour.
        """
        now = datetime.now()
        to_delete = []

        for request_id, files in self.animation_files.items():
            age = (now - files['timestamp']).total_seconds()
            if age > 3600:  # 1 hour
                to_delete.append(request_id)

        for request_id in to_delete:
            files = self.animation_files[request_id]
            Path(files['script_path']).unlink(missing_ok=True)
            Path(files['video_path']).unlink(missing_ok=True)
            del self.animation_files[request_id]
            print(f"🗑️ Cleaned up animation: {request_id}")


async def entrypoint(ctx: JobContext):
    """Main entry point - the ONLY agent you need to run"""

    print("\n" + "="*80)
    print(f"🎯 MAIN ORCHESTRATOR AGENT")
    print(f"📍 Room: {ctx.room.name}")
    print(f"🎤 Transcription: OpenAI Whisper + Silero VAD")
    print(f"🧠 AI Analysis: DigitalOcean Gradient (llama3.3-70b-instruct)")
    print(f"⚡ Features: Pre-computed summaries + Auto Q&A")
    print("="*80 + "\n")

    # Initialize components
    print("🎤 Initializing STT & VAD...")
    stt = openai.STT()
    vad = silero.VAD.load()

    print("🧠 Initializing Orchestrator...")
    orchestrator = CentralOrchestrator()

    active_transcriptions = {}

    # Background task: Pre-compute summaries every 5 seconds
    async def background_precompute():
        """Background task for dashboard pre-computation"""
        await asyncio.sleep(10)  # Initial wait

        while True:
            try:
                cache_data = await orchestrator.precompute_dashboard()

                if cache_data:
                    payload = json.dumps(cache_data).encode('utf-8')
                    await ctx.room.local_participant.publish_data(
                        payload=payload,
                        topic='lk.dashboard-cache',
                        reliable=True
                    )
                    print(f"📤 Published dashboard cache\n")

                # Cleanup old animations
                await orchestrator.cleanup_old_animations()

            except Exception as e:
                print(f"❌ Background error: {e}")

            await asyncio.sleep(5)

    # Transcription handler
    async def transcribe_track(track: rtc.Track, participant: rtc.RemoteParticipant):
        """Handle audio transcription"""
        print(f"\n🎤 TRANSCRIBING - {participant.identity}")

        role = "teacher" if "teacher" in participant.identity.lower() else "student"
        print(f"   Role: {role}")

        audio_stream = rtc.AudioStream(track)
        stream_adapter = agents.stt.StreamAdapter(stt=stt, vad=vad)
        stt_stream = stream_adapter.stream()

        async def process():
            print(f"👂 Listening to {participant.identity}...")
            try:
                async for event in stt_stream:
                    if event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT and event.alternatives:
                        text = event.alternatives[0].text
                        if text.strip():
                            print(f"\n📝 [{role.upper()}] {participant.identity}: {text}")

                            # 1. Publish transcription
                            await ctx.room.local_participant.publish_data(
                                payload=text.encode('utf-8'),
                                topic='lk.transcription',
                                reliable=True
                            )

                            # 2. Add to orchestrator
                            orchestrator.add_message(participant.identity, text, role)

                            # 3. Answer student questions
                            if orchestrator.is_question(text) and role == "student":
                                print(f"❓ Question detected!")
                                answer = await orchestrator.answer_question(text)
                                if answer:
                                    print(f"🤖 Answer: {answer}\n")

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
                print(f"❌ Transcription error: {e}")
                import traceback
                traceback.print_exc()

        async def push():
            try:
                async for event in audio_stream:
                    stt_stream.push_frame(event.frame)
            except Exception as e:
                print(f"❌ Audio push error: {e}")
            finally:
                await stt_stream.aclose()

        await asyncio.gather(push(), process())

    # Event handlers
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"\n🎤 AUDIO TRACK - {participant.identity}")
            task = asyncio.create_task(transcribe_track(track, participant))
            active_transcriptions[participant.identity] = task

    def on_track_unsubscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if participant.identity in active_transcriptions:
            active_transcriptions[participant.identity].cancel()
            del active_transcriptions[participant.identity]

    # Handle animation requests from frontend
    async def handle_data_received(data: rtc.DataPacket):
        """Handle incoming data from frontend"""
        if data.topic == 'lk.animation-request':
            try:
                payload = json.loads(data.data.decode('utf-8'))
                question = payload.get('question')
                request_id = payload.get('requestId')

                if not question or not request_id:
                    print("❌ Invalid animation request")
                    return

                print(f"\n🎬 Animation request received: {question}")

                # Send acknowledgment
                ack_payload = json.dumps({
                    'requestId': request_id,
                    'status': 'processing'
                }).encode('utf-8')
                await ctx.room.local_participant.publish_data(
                    payload=ack_payload,
                    topic='lk.animation-processing',
                    reliable=True
                )

                # Generate animation
                result = await orchestrator.generate_manim_animation(question, request_id)

                if result['success']:
                    # Publish success
                    success_payload = json.dumps({
                        'requestId': request_id,
                        'videoId': result['video_id'],
                        'duration': result.get('duration', 0)
                    }).encode('utf-8')
                    await ctx.room.local_participant.publish_data(
                        payload=success_payload,
                        topic='lk.animation-complete',
                        reliable=True
                    )
                else:
                    # Publish error
                    error_payload = json.dumps({
                        'requestId': request_id,
                        'error': result['error']
                    }).encode('utf-8')
                    await ctx.room.local_participant.publish_data(
                        payload=error_payload,
                        topic='lk.animation-error',
                        reliable=True
                    )

            except Exception as e:
                print(f"❌ Error handling animation request: {e}")

    # Register handlers BEFORE connecting
    ctx.room.on("track_subscribed", on_track_subscribed)
    ctx.room.on("track_unsubscribed", on_track_unsubscribed)
    ctx.room.on("data_received", handle_data_received)

    # Connect
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ Connected to room: {ctx.room.name}")

    # Handle existing participants
    print(f"\n🔍 Checking existing participants...")
    for participant in ctx.room.remote_participants.values():
        print(f"  - {participant.identity}")
        for track_pub in participant.track_publications.values():
            if track_pub.subscribed and track_pub.track and track_pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"    🎤 Starting transcription...")
                task = asyncio.create_task(transcribe_track(track_pub.track, participant))
                active_transcriptions[participant.identity] = task

    # Start background task
    print("\n🚀 Starting background pre-compute (every 5 sec)...")
    asyncio.create_task(background_precompute())

    print("\n" + "="*80)
    print("✅ ORCHESTRATOR ACTIVE")
    print("🎤 Transcribing all speech")
    print("🧠 Pre-computing summaries every 5 seconds")
    print("❓ Auto-answering student questions")
    print("📊 Dashboard buttons will activate in 10-15 seconds")
    print("="*80 + "\n")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
