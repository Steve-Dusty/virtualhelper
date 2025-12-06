import asyncio
import os
from livekit import rtc
from livekit.rtc import AudioFrame
from langchain_gradient import ChatGradient
import httpx
from dotenv import load_dotenv

load_dotenv()


class SimpleClassroomAgent:
    """Simple agent that joins LiveKit and summarizes conversations"""

    def __init__(self):
        self.transcript = []
        self.llm = ChatGradient(
            model="llama3.3-70b-instruct",
            api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
        )
        self.room = rtc.Room()

    async def get_token(self):
        """Get token from your backend"""
        backend_url = os.getenv("BACKEND_URL", "http://localhost:3001")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{backend_url}/token",
                params={"room": "main-room", "username": "AI-Agent", "role": "student"}
            )
            data = response.json()
            return data["token"]

    async def transcribe_audio(self, audio_data):
        """Send audio to Deepgram for transcription"""
        # This is a placeholder - you'd integrate with Deepgram API here
        # For now, we'll skip real-time transcription
        pass

    def add_transcript(self, speaker: str, text: str):
        """Add transcript line"""
        self.transcript.append(f"{speaker}: {text}")
        print(f"📝 {speaker}: {text}")

    async def get_summary(self):
        """Generate summary using Gradient AI"""
        if len(self.transcript) < 5:
            return

        recent = "\n".join(self.transcript[-20:])

        messages = [
            ("system", "You are analyzing a classroom conversation. Be concise."),
            ("human", f"Summarize the key points from this conversation:\n\n{recent}")
        ]

        response = await asyncio.to_thread(self.llm.invoke, messages)
        print(f"\n📊 SUMMARY:\n{response.content}\n")

    async def on_data_received(self, data_packet: rtc.DataPacket):
        """Handle data messages (like chat)"""
        if data_packet.topic == "transcript":
            # If someone sends transcript data
            text = data_packet.data.decode()
            participant = data_packet.participant
            self.add_transcript(participant.identity, text)

            # Generate summary every 10 messages
            if len(self.transcript) % 10 == 0:
                await self.get_summary()

    async def connect_and_listen(self):
        """Connect to LiveKit room and listen"""
        print("🤖 Starting AI Agent...")

        # Get token
        token = await self.get_token()
        livekit_url = os.getenv("LIVEKIT_URL")

        # Connect
        await self.room.connect(livekit_url, token)
        print(f"✅ Connected to room: {self.room.name}")

        # Listen for data packets (if you send transcripts via data channel)
        @self.room.on("data_received")
        def on_data(data_packet: rtc.DataPacket):
            asyncio.create_task(self.on_data_received(data_packet))

        # Listen for track subscriptions (audio)
        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.TrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"🎤 Listening to {participant.identity}")
                # You could process audio here with Deepgram
                # For now, we'll rely on data messages

        print("👂 Agent is listening...")
        print("💡 Tip: Send transcripts via data channel with topic 'transcript'")

        # Keep running
        while True:
            await asyncio.sleep(1)


async def main():
    agent = SimpleClassroomAgent()
    await agent.connect_and_listen()


if __name__ == "__main__":
    asyncio.run(main())
