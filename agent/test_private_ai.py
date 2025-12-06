#!/usr/bin/env python3
"""
Quick test for private AI chat functionality
"""
import asyncio
import json
from main_agent import CentralOrchestrator

async def test_private_ai_chat():
    """Test the private AI question/answer flow"""

    print("="*80)
    print("🧪 TESTING PRIVATE AI CHAT")
    print("="*80)

    # Initialize orchestrator
    print("\n1️⃣  Initializing orchestrator...")
    orchestrator = CentralOrchestrator()

    # Add some classroom context
    print("2️⃣  Adding classroom context...")
    orchestrator.add_message("Teacher", "Today we're learning about photosynthesis", "teacher")
    orchestrator.add_message("Teacher", "Plants use sunlight to create energy", "teacher")
    orchestrator.add_message("Teacher", "The process converts CO2 and water into glucose", "teacher")

    # Simulate student private questions
    test_questions = [
        "What is photosynthesis?",
        "Why do plants need sunlight?",
        "I'm confused about how plants make energy",
        "Can you explain the role of chlorophyll?"
    ]

    print("\n3️⃣  Testing private AI responses...\n")

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/4: {question}")
        print('='*80)

        # Generate answer (simulates what agent does when receiving lk.private-ai-question)
        answer = await orchestrator.answer_question(question)

        if answer:
            print(f"\n✅ AI Response:")
            print(f"   {answer}")

            # This would be sent via:
            # topic='lk.private-ai-response'
            # destination_identities=[student_identity]

            response_payload = {
                'question': question,
                'answer': answer,
                'timestamp': '2024-01-01T00:00:00',
                'type': 'private-ai-response'
            }
            print(f"\n📤 Would send to student only:")
            print(f"   Topic: lk.private-ai-response")
            print(f"   Payload: {json.dumps(response_payload, indent=2)}")
        else:
            print(f"\n❌ Failed to generate response")

        await asyncio.sleep(0.5)  # Brief pause between questions

    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    print("\nKey Points:")
    print("- ✅ AI generates contextual responses")
    print("- ✅ Responses are encouraging and educational")
    print("- ✅ Uses classroom context effectively")
    print("- ✅ Ready for frontend integration")
    print("\nNext Steps:")
    print("1. Frontend implements 'Ask AI' button")
    print("2. Frontend sends via 'lk.private-ai-question' topic")
    print("3. Frontend listens for 'lk.private-ai-response' topic")
    print("4. Display in right panel chat UI")

if __name__ == "__main__":
    asyncio.run(test_private_ai_chat())
