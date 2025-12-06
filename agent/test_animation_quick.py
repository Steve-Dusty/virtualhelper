#!/usr/bin/env python3
"""
Quick test script for animation generation
Run this to test if animations work properly
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main_agent import CentralOrchestrator

async def test_animation():
    """Test animation generation with a simple math question"""

    print("="*80)
    print("🧪 TESTING ANIMATION GENERATION")
    print("="*80)

    # Initialize orchestrator
    print("\n1️⃣  Initializing orchestrator...")
    orchestrator = CentralOrchestrator()

    # Add some classroom context
    print("2️⃣  Adding classroom context...")
    orchestrator.add_message("Teacher", "Today we're learning about basic algebra", "teacher")
    orchestrator.add_message("Teacher", "Let's start with simple equations like x + 5 = 10", "teacher")

    # Test question
    question = "Can you explain how to solve x + 5 = 10 visually?"
    request_id = "test-123"

    print(f"\n3️⃣  Generating animation...")
    print(f"   Question: {question}")
    print(f"   Request ID: {request_id}")
    print("\n" + "-"*80)

    # Generate animation
    result = await orchestrator.generate_manim_animation(question, request_id)

    print("\n" + "="*80)
    print("📊 RESULT")
    print("="*80)

    if result['success']:
        print("✅ SUCCESS!")
        print(f"   Video ID: {result['video_id']}")

        video_path = f"/tmp/output_{request_id}.mp4"
        if Path(video_path).exists():
            file_size = Path(video_path).stat().st_size
            print(f"   Video path: {video_path}")
            print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            print(f"\n🎬 You can view the video at: {video_path}")
        else:
            print(f"   ⚠️  Warning: Video file not found at {video_path}")
    else:
        print("❌ FAILED!")
        print(f"   Error: {result['error']}")

        # Check if debug file exists
        debug_path = f"/tmp/failed_manim_{request_id}.py"
        if Path(debug_path).exists():
            print(f"\n🔍 Debug: Failed code saved to {debug_path}")
            print("\nTo see what failed, run:")
            print(f"   cat {debug_path}")

    print("="*80)
    return result['success']

if __name__ == "__main__":
    success = asyncio.run(test_animation())
    sys.exit(0 if success else 1)
