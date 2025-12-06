# Classroom AI Agent

A LiveKit agent that listens to classroom conversations and provides real-time analysis and summaries.

## Features

- Real-time speech-to-text transcription using Deepgram
- Conversation analysis using DigitalOcean Gradient AI (Llama 3.3 70B)
- Automatic summaries every 10 messages
- Tracks all participants (teacher and students)

## Setup

### 1. Install Python Dependencies

```bash
cd agent

# Using pip
pip install -r requirements.txt

# Or using uv (recommended)
pip install uv
uv pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env` and add your API keys:

```bash
LIVEKIT_URL=wss://mlh-y84pgvt9.livekit.cloud
LIVEKIT_API_KEY=APIZBgZLYQuQRxQ
LIVEKIT_API_SECRET=2bczAqYSjtWQHTYWEQneizMD2H1mJsBLH8JxeoOFJaI
DIGITALOCEAN_INFERENCE_KEY=your-gradient-key-here
DEEPGRAM_API_KEY=your-deepgram-key-here
```

**Get API Keys:**
- DigitalOcean Gradient AI: https://cloud.digitalocean.com/ → AI & ML → Serverless Inference
- Deepgram: https://console.deepgram.com/ (free tier available)

### 3. Run the Agent

```bash
python agent.py dev
```

The agent will:
1. Connect to your LiveKit room
2. Listen to all audio tracks
3. Transcribe speech in real-time
4. Log transcripts to console
5. Generate summaries every 10 messages

## How It Works

1. **Agent joins room**: Connects as a participant (doesn't publish video/audio)
2. **Subscribes to audio**: Listens to teacher and all students
3. **Transcribes**: Uses Deepgram to convert speech to text
4. **Analyzes**: Uses GPT-4 to summarize key points
5. **Logs**: Outputs transcripts and summaries

## Output Example

```
🤖 Agent starting for room: main-room
✅ Connected to room
🎤 Subscribed to Teacher's audio
📝 Teacher: Today we're going to learn about photosynthesis
🎤 Subscribed to Student-abc123's audio
📝 Student-abc123: What is chlorophyll?
📝 Teacher: Great question! Chlorophyll is the green pigment...
📊 SUMMARY: The teacher is explaining photosynthesis. A student asked about chlorophyll, and the teacher explained it's the green pigment that helps plants convert sunlight to energy.
```

## Customization

### Change Summary Frequency

Edit `agent.py` line 89:
```python
if len(analyzer.transcript) % 10 == 0:  # Change 10 to your desired number
```

### Use Different LLM Model

Change the Gradient AI model in `agent.py`:
```python
self.llm = ChatGradient(
    model="llama3-8b-instruct",  # Smaller, faster model
    api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
)
```

### Publish Summaries to Room

Add this to send summaries as data messages:
```python
await ctx.room.local_participant.publish_data(
    summary.encode(),
    topic="summary"
)
```

## Deployment

Deploy to LiveKit Cloud:
```bash
lk agent create classroom-agent
```

Or run on your own server with systemd/pm2.
