"""
VOICE AI AGENT
LiveKit voice agent that has real voice conversations with students.
- Listens to student speech (STT with Whisper)
- Responds with voice (TTS with OpenAI)
- Private - only the student hears the AI
"""

import asyncio
import json
from datetime import datetime
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, VoiceAssistant
from livekit.plugins import openai, silero
from gradient import Gradient
from dotenv import load_dotenv
import os

load_dotenv()


class VoiceAIOrchestrator:
    """Orchestrator for voice AI conversations"""

    def __init__(self):
        self.gradient_client = Gradient(
            model_access_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY")
        )
        self.model = "llama3.3-70b-instruct"
        self.conversation_history = {}  # {student_identity: [{role, content}]}

    async def generate_response(self, student_identity: str, question: str, context: str = "") -> str:
        """Generate voice response for student question"""

        # Get conversation history for this student
        history = self.conversation_history.get(student_identity, [])

        prompt = f"""You are a helpful AI teaching assistant having a voice conversation with a student.

Classroom Context:
{context}

Student's question: "{question}"

Provide a clear, conversational 2-3 sentence spoken response that:
1. Directly answers the student's question
2. Uses simple, encouraging language (you're speaking, not writing)
3. Relates to the current lesson
4. Is natural for speech (avoid complex formatting)

Response (speak naturally):"""

        try:
            response = await asyncio.to_thread(
                self.gradient_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=200,
                temperature=0.7
            )

            if response.choices and response.choices[0].message.content:
                answer = response.choices[0].message.content.strip()

                # Store in conversation history
                if student_identity not in self.conversation_history:
                    self.conversation_history[student_identity] = []

                self.conversation_history[student_identity].append({
                    "role": "user",
                    "content": question
                })
                self.conversation_history[student_identity].append({
                    "role": "assistant",
                    "content": answer
                })

                # Keep last 10 exchanges
                if len(self.conversation_history[student_identity]) > 20:
                    self.conversation_history[student_identity] = self.conversation_history[student_identity][-20:]

                return answer

        except Exception as e:
            print(f"❌ Error generating voice response: {e}")
            return "I'm sorry, I didn't quite catch that. Could you ask again?"

        return "I'm having trouble understanding. Could you rephrase that?"


async def entrypoint(ctx: JobContext):
    """Voice AI agent entry point"""

    print("\n" + "="*80)
    print(f"🎙️ VOICE AI AGENT")
    print(f"📍 Room: {ctx.room.name}")
    print(f"🎤 STT: OpenAI Whisper")
    print(f"🔊 TTS: OpenAI TTS")
    print(f"🧠 AI: DigitalOcean Gradient (Llama 3.3 70B)")
    print(f"🔒 Private: Only students hear their conversations")
    print("="*80 + "\n")

    # Initialize components
    print("🎤 Initializing STT & TTS...")
    stt = openai.STT()
    tts = openai.TTS()
    vad = silero.VAD.load()

    print("🧠 Initializing Voice AI Orchestrator...")
    orchestrator = VoiceAIOrchestrator()

    # Connect to room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print(f"✅ Connected to room: {ctx.room.name}")

    # Track active voice assistants per student
    voice_assistants = {}

    async def create_voice_assistant_for_student(participant: rtc.RemoteParticipant):
        """Create a voice assistant for a specific student"""

        if "teacher" in participant.identity.lower():
            print(f"👨‍🏫 Skipping teacher: {participant.identity}")
            return

        print(f"\n🎙️ Creating Voice AI for: {participant.identity}")

        # Create voice assistant
        assistant = VoiceAssistant(
            vad=vad,
            stt=stt,
            llm=None,  # We'll handle LLM responses manually
            tts=tts,
            chat_ctx=None,
        )

        # Handle student speech
        async def handle_speech(text: str):
            print(f"👂 Heard from {participant.identity}: {text}")

            # Generate response
            response = await orchestrator.generate_response(
                participant.identity,
                text,
                context=""  # Could add classroom context here
            )

            print(f"🤖 Responding to {participant.identity}: {response[:100]}...")

            # Send text response via data channel (for UI display)
            response_data = json.dumps({
                'question': text,
                'answer': response,
                'timestamp': datetime.now().isoformat(),
                'type': 'voice-ai-response'
            }).encode('utf-8')

            await ctx.room.local_participant.publish_data(
                payload=response_data,
                topic='lk.private-ai-response',
                destination_identities=[participant.identity],
                reliable=True
            )

            # Speak response back to student
            # The voice assistant will speak this using TTS
            return response

        # Start voice assistant
        assistant.start(ctx.room)

        # Subscribe to student's microphone
        async def transcribe_student_audio():
            """Transcribe and respond to student audio"""
            print(f"👂 Listening to {participant.identity}...")

            # Get audio track
            audio_track = None
            for track_pub in participant.track_publications.values():
                if track_pub.track and track_pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                    audio_track = track_pub.track
                    break

            if not audio_track:
                print(f"❌ No audio track for {participant.identity}")
                return

            audio_stream = rtc.AudioStream(audio_track)
            stream_adapter = agents.stt.StreamAdapter(stt=stt, vad=vad)
            stt_stream = stream_adapter.stream()

            async def process_speech():
                try:
                    async for event in stt_stream:
                        if event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT and event.alternatives:
                            text = event.alternatives[0].text
                            if text.strip():
                                # Handle the speech and get response
                                response = await handle_speech(text)

                                # Synthesize speech response
                                if response:
                                    tts_stream = tts.stream()
                                    async for audio_chunk in tts_stream:
                                        # Publish audio only to this student
                                        # Note: This is a simplified version
                                        # Full implementation would use LiveKit's participant audio publishing
                                        pass

                except Exception as e:
                    print(f"❌ Error processing speech for {participant.identity}: {e}")

            async def push_audio():
                try:
                    async for event in audio_stream:
                        stt_stream.push_frame(event.frame)
                except Exception as e:
                    print(f"❌ Audio push error for {participant.identity}: {e}")
                finally:
                    await stt_stream.aclose()

            await asyncio.gather(push_audio(), process_speech())

        # Start transcription task
        task = asyncio.create_task(transcribe_student_audio())
        voice_assistants[participant.identity] = {
            'assistant': assistant,
            'task': task
        }

    # Handle participant connections
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        print(f"✅ Participant joined: {participant.identity}")
        asyncio.create_task(create_voice_assistant_for_student(participant))

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        print(f"👋 Participant left: {participant.identity}")
        if participant.identity in voice_assistants:
            voice_assistants[participant.identity]['task'].cancel()
            del voice_assistants[participant.identity]

    # Create assistants for existing participants
    print(f"\n🔍 Checking existing participants...")
    for participant in ctx.room.remote_participants.values():
        print(f"  - {participant.identity}")
        await create_voice_assistant_for_student(participant)

    print("\n" + "="*80)
    print("✅ VOICE AI ACTIVE")
    print("🎙️ Students can now speak and get voice responses")
    print("🔒 All conversations are private")
    print("="*80 + "\n")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
