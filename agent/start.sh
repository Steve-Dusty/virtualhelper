#!/bin/bash
# MAIN ORCHESTRATOR AGENT - The ONLY agent you need to run!

echo "🎯 Starting Main Orchestrator Agent..."
echo "================================"
echo ""
echo "Features:"
echo "  🎤 Real-time transcription (OpenAI Whisper + VAD)"
echo "  🧠 AI Analysis (DigitalOcean Gradient - Llama 3.3 70B)"
echo "  ⚡ Pre-computes summaries every 5 seconds"
echo "  📊 Instant dashboard responses"
echo "  ❓ Auto-answers student questions"
echo ""
echo "This is the ONLY agent - no more switching!"
echo "================================"
echo ""

cd "$(dirname "$0")"
python3 main_agent.py dev
