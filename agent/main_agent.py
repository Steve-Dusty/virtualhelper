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
        self.manim_timeout = 120  # seconds (increased for longer, higher-quality animations)

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
        prompt = f"""You are a Manim expert creating 3Blue1Brown-style educational animations.

Student Question: "{question}"

Classroom Context:
{context}

Generate a complete, comprehensive Manim script that:

ANIMATION REQUIREMENTS:
1. Duration: Create a 15-20 second comprehensive animation
2. Sequential & Clear: NO overlapping animations - each element must be introduced sequentially
3. Style: 3Blue1Brown aesthetic with smooth, elegant animations
4. Pacing: Use run_time=1.5-2 for main animations, wait(1) between major sections

🚨 CRITICAL: NO OVERLAPPING TEXT/EQUATIONS 🚨
- NEVER place multiple equations or text in the same position
- Use VERTICAL SPACING: .shift(UP*3), .shift(UP*2), .shift(UP), ORIGIN (center), .shift(DOWN), .shift(DOWN*2), .shift(DOWN*3)
- Use HORIZONTAL SPACING: .shift(LEFT*3), .shift(LEFT*2), .shift(LEFT), ORIGIN (center), .shift(RIGHT), .shift(RIGHT*2), .shift(RIGHT*3)
- Each new element MUST have a different position than previous elements
- Example: If one equation is at .shift(UP*2), put the next at ORIGIN, then .shift(DOWN*2)
- Use .next_to() to position elements relative to others with proper buffer
- Example: text2.next_to(text1, DOWN, buff=0.5)
- IMPORTANT: In Manim, the center is ORIGIN (not CENTER). Elements without .shift() default to ORIGIN

VISUAL DIVERSITY - USE MULTIPLE OBJECT TYPES:
Beyond just text and equations, include:
- GRAPHS: Use Axes() with plot() to show functions, trends, relationships
- CHARTS: Use BarChart() for comparisons, data visualization
- GEOMETRIC SHAPES: Circles, Squares, Rectangles, Polygons to represent concepts
- ARROWS: Vector arrows, curved arrows to show flow and relationships
- NUMBER LINES: NumberLine() for sequences, ranges, intervals
- COORDINATE SYSTEMS: Axes for plotting points, functions, transformations
- DIAGRAMS: Combine shapes to create conceptual diagrams
- ANIMATIONS: Move objects, transform shapes, show cause-and-effect visually

3BLUE1BROWN STYLING FOR MATH CONCEPTS:
- Colors: BLUE (#58C4DD) for primary concepts, YELLOW (#FFFF00) for highlights, GREEN (#83C167) for results
- Animations: Use Transform, FadeIn, Write, Create, Indicate, Flash for emphasis
- Layout: Center main concepts, use arrows to show relationships
- Text: Large titles (font_size=48), clear explanations (font_size=36)
- Shapes: Clean geometric shapes with smooth transitions

STRUCTURE (Follow this exactly):
1. Title scene (2-3 seconds): Fade in the title, wait, fade out
2. Setup (3-4 seconds): Introduce the problem/concept with text and basic shapes
3. Main explanation (8-10 seconds): Step-by-step visual breakdown with GRAPHS/CHARTS/DIAGRAMS
4. Conclusion (2-3 seconds): Show final result with emphasis

CRITICAL SECURITY RULES (Code will be rejected if violated):
- ONLY import from manim: "from manim import *" (NO other imports!)
- NO file operations: NO open(), read(), write(), Path()
- NO dangerous functions: NO eval(), exec(), __import__()
- NO system operations: NO os., sys., subprocess
- NO network operations: NO requests, urllib, socket
- NO infinite loops: NO "while True:"
- MUST have: class ExplainScene(Scene):

TECHNICAL RULES:
- Use Text() for ALL text including math (e.g., Text("a² + b² = c²"))
- NO Tex, MathTex, or LaTeX - ONLY Text()
- Use Manim built-in colors: BLUE, YELLOW, GREEN, RED, WHITE, GRAY, ORANGE, PURPLE, PINK
- Each animation: run_time between 1.5-2 seconds
- Add self.wait(1) between major animation sequences
- NO overlapping: Use self.play() one at a time, then self.wait()
- Use simple Manim objects: Circle, Square, Rectangle, Arrow, Line, Dot, Text, Polygon, Axes, NumberLine, BarChart
- Available position constants: ORIGIN (center), UP, DOWN, LEFT, RIGHT (combine with * for multiples)
- DO NOT use undefined constants like CENTER - use ORIGIN instead

EXAMPLE STRUCTURE WITH PROPER SPACING AND VISUAL DIVERSITY:
```python
from manim import *

class ExplainScene(Scene):
    def construct(self):
        # 1. TITLE (2-3 sec) - Position at TOP
        title = Text("Pythagorean Theorem", font_size=48, color=BLUE).shift(UP*2.5)
        self.play(Write(title), run_time=2)
        self.wait(1)
        self.play(FadeOut(title), run_time=1)

        # 2. SETUP (3-4 sec) - Position at TOP, then move
        setup_text = Text("For right triangles:", font_size=36).shift(UP*3)
        self.play(FadeIn(setup_text), run_time=1.5)
        self.wait(1)

        # 3. MAIN CONTENT (8-10 sec) - MULTIPLE OBJECTS WITH DIFFERENT POSITIONS
        # Draw triangle at CENTER-LEFT (not overlapping with text)
        triangle = Polygon(LEFT*2+DOWN, LEFT*2+UP*2, RIGHT+DOWN, color=BLUE).shift(LEFT*2)
        self.play(Create(triangle), run_time=2)
        self.wait(1)

        # Add labels at DIFFERENT positions using .next_to()
        label_a = Text("a = 3", color=YELLOW, font_size=28).next_to(triangle, LEFT, buff=0.3)
        self.play(Write(label_a), run_time=1.5)
        self.wait(0.5)

        label_b = Text("b = 4", color=YELLOW, font_size=28).next_to(triangle, UP, buff=0.3)
        self.play(Write(label_b), run_time=1.5)
        self.wait(0.5)

        label_c = Text("c = ?", color=YELLOW, font_size=28).next_to(triangle, RIGHT, buff=0.3)
        self.play(Write(label_c), run_time=1.5)
        self.wait(0.5)

        # Add GRAPH or VISUAL on the RIGHT side (not overlapping!)
        # Example: Show the relationship as a graph
        axes = Axes(
            x_range=[0, 5, 1], y_range=[0, 5, 1],
            x_length=3, y_length=3,
            axis_config={{"color": GRAY}}
        ).shift(RIGHT*3.5)

        graph = axes.plot(lambda x: (x**2)**0.5, color=GREEN)
        self.play(Create(axes), run_time=1.5)
        self.play(Create(graph), run_time=1.5)
        self.wait(1)

        # 4. CONCLUSION (2-3 sec) - Position at BOTTOM (separate from everything else!)
        result = Text("a² + b² = c²", font_size=40, color=GREEN).shift(DOWN*2.5)
        self.play(Write(result), run_time=2)
        self.play(Flash(result, color=YELLOW), run_time=1)

        final_answer = Text("3² + 4² = 5²", font_size=36, color=YELLOW).next_to(result, DOWN, buff=0.5)
        self.play(Write(final_answer), run_time=1)
        self.wait(1)
```

KEY SPACING RULES IN THIS EXAMPLE:
- Title: UP*2.5 (top of screen)
- Setup text: UP*3 (very top)
- Triangle: LEFT*2 (left side, centered vertically)
- Labels: Use .next_to() with buff=0.3 (positioned relative to triangle)
- Graph/Axes: RIGHT*3.5 (right side, not overlapping triangle)
- Result: DOWN*2.5 (bottom of screen)
- Final answer: .next_to(result, DOWN, buff=0.5) (below result)

NEVER put two elements in the same position! Each must have unique placement!

Return ONLY the Python code following this structure:"""

        try:
            # Generate code
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=1500,  # Increased for comprehensive animations
                temperature=0.4  # Slightly higher for more creative animations
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
                # Save failed code for debugging
                debug_path = f"/tmp/failed_manim_{request_id}.py"
                with open(debug_path, 'w') as f:
                    f.write(code)
                print(f"💾 Failed code saved to: {debug_path}")
                return {"success": False, "error": "Generated code failed security validation. Check agent logs for details."}

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
        print(f"\n🔒 Validating generated code...")

        # Check for allowed imports (only manim)
        import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]

        for line in import_lines:
            # Allow: from manim import *, import manim
            if not (line.startswith('from manim ') or line.startswith('import manim')):
                print(f"❌ VALIDATION FAILED: Forbidden import detected")
                print(f"   Line: {line}")
                return False

        # Check for dangerous operations
        dangerous_patterns = {
            r'\bopen\s*\(': 'File operations (open)',
            r'\beval\s*\(': 'Code execution (eval)',
            r'\bexec\s*\(': 'Code execution (exec)',
            r'\b__import__': 'Dynamic imports',
            r'\bsubprocess\.': 'System calls (subprocess)',
            r'\bos\.': 'OS operations',
            r'\bsys\.': 'System operations',
            r'requests\.': 'Network requests',
            r'urllib\.': 'Network urllib',
            r'socket\.': 'Network socket',
            r'while\s+True\s*:': 'Infinite loops (while True)'
        }

        for pattern, description in dangerous_patterns.items():
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                print(f"❌ VALIDATION FAILED: {description}")
                print(f"   Pattern: {pattern}")
                print(f"   Matched: {match.group()}")
                print(f"   Context: ...{code[max(0, match.start()-30):match.end()+30]}...")
                return False

        # Must contain required class
        if 'class ExplainScene(Scene):' not in code:
            print(f"❌ VALIDATION FAILED: Missing required class 'ExplainScene(Scene)'")
            return False

        print(f"✅ Code validation passed!")
        return True

    def _run_manim(self, script_path: str, output_path: str, request_id: str) -> dict:
        """
        Execute Manim script with timeout and error handling.
        """
        import shutil
        import glob

        try:
            # Create output directory for this render
            output_dir = f"/tmp/manim_output_{request_id}"
            Path(output_dir).mkdir(exist_ok=True)

            # Manim command: medium quality for better visuals
            cmd = [
                'manim',
                '-qm',  # Medium quality (720p, good balance)
                '--format=mp4',
                '--fps=30',  # Smooth 30fps
                f'--media_dir={output_dir}',
                script_path,
                'ExplainScene'
            ]

            print(f"🎬 Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.manim_timeout
            )

            print(f"📤 Manim stdout: {result.stdout[-500:]}")
            print(f"📤 Manim stderr: {result.stderr[-500:]}")

            if result.returncode == 0:
                # Find the generated video file (Manim creates nested structure)
                video_files = glob.glob(f"{output_dir}/**/ExplainScene.mp4", recursive=True)

                if video_files:
                    # Move first found video to expected location
                    shutil.move(video_files[0], output_path)
                    # Cleanup temp directory
                    shutil.rmtree(output_dir, ignore_errors=True)
                    print(f"✅ Video saved to: {output_path}")
                    return {"success": True}
                else:
                    print(f"❌ No video files found in {output_dir}")
                    return {"success": False, "error": "Video file not found after rendering"}
            else:
                error_msg = result.stderr[-500:] if result.stderr else result.stdout[-500:]
                print(f"❌ Manim error: {error_msg}")
                return {"success": False, "error": f"Manim rendering failed: {error_msg}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Animation generation timed out (60s)"}
        except Exception as e:
            import traceback
            traceback.print_exc()
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
    async def handle_data_received_async(data: rtc.DataPacket):
        """Handle incoming data from frontend (async)"""
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

    # Sync wrapper for data_received event
    def on_data_received(data: rtc.DataPacket):
        """Sync wrapper that creates task for async handler"""
        asyncio.create_task(handle_data_received_async(data))

    # Register handlers BEFORE connecting
    ctx.room.on("track_subscribed", on_track_subscribed)
    ctx.room.on("track_unsubscribed", on_track_unsubscribed)
    ctx.room.on("data_received", on_data_received)

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
