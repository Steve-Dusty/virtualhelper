#!/bin/bash

# Classroom AI Agent Startup Script

echo "🤖 Starting Classroom AI Agent..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and add your API keys"
    exit 1
fi

# Check for required API keys
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_key_here" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in .env"
    echo "Get your key at: https://platform.openai.com/api-keys"
    echo ""
fi

if [ -z "$DEEPGRAM_API_KEY" ] || [ "$DEEPGRAM_API_KEY" = "your_deepgram_key_here" ]; then
    echo "⚠️  Warning: DEEPGRAM_API_KEY not set in .env"
    echo "Get your key at: https://console.deepgram.com/"
    echo ""
fi

echo "🚀 Launching agent..."
echo ""

python3 agent.py dev
