"""
Test script for Manim animation generation
"""
import asyncio
from main_agent import CentralOrchestrator
import os
from pathlib import Path

async def test_manim_generation():
    """Test the Manim animation generation pipeline"""

    print("🧪 Testing Manim Animation Generation\n")
    print("="*80)

    # Initialize orchestrator
    orchestrator = CentralOrchestrator()

    # Add some context
    orchestrator.add_message("Teacher", "Today we're learning about the Pythagorean theorem", "teacher")
    orchestrator.add_message("Teacher", "It states that a² + b² = c² for right triangles", "teacher")

    # Test question
    test_question = "Can you explain the Pythagorean theorem visually?"
    request_id = "test-123-456"

    print(f"\n📝 Question: {test_question}")
    print(f"🆔 Request ID: {request_id}")
    print(f"\n🎬 Generating animation...\n")

    # Generate animation
    result = await orchestrator.generate_manim_animation(test_question, request_id)

    print("\n" + "="*80)
    print("📊 RESULT:")
    print("="*80)

    if result['success']:
        print("✅ SUCCESS!")
        print(f"   Video ID: {result['video_id']}")

        video_path = f"/tmp/output_{request_id}.mp4"
        if Path(video_path).exists():
            file_size = Path(video_path).stat().st_size
            print(f"   Video file: {video_path}")
            print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        else:
            print(f"   ⚠️ Warning: Video file not found at {video_path}")
    else:
        print("❌ FAILED!")
        print(f"   Error: {result['error']}")

    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_manim_generation())
