#!/bin/bash
# Start the LiveKit agent

cd "$(dirname "$0")"

echo "🤖 Starting LiveKit Classroom Agent..."
echo "📡 Connecting to: $LIVEKIT_URL"
echo ""

python3 agent.py dev
