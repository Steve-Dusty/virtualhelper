#!/usr/bin/env python3
"""Test Gradient API integration"""

import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Gradient SDK...")
print("="*60)

# Test 1: Direct Gradient SDK
try:
    from gradient import Gradient

    inference_client = Gradient(
        model_access_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY")
    )

    print("\n✅ Test 1: Direct Gradient SDK")
    inference_response = inference_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "What is 2+2? Answer in one sentence.",
            }
        ],
        model="openai-gpt-oss-120b",
        max_tokens=50
    )

    print(f"Response: {inference_response.choices[0].message.content}")

except Exception as e:
    print(f"❌ Test 1 failed: {e}")

# Test 2: LangChain Gradient
try:
    from langchain_gradient import ChatGradient
    from langchain_core.messages import HumanMessage

    print("\n✅ Test 2: LangChain Gradient")

    llm = ChatGradient(
        gradient_api_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY"),
        model="openai-gpt-oss-120b",
        max_tokens=50,
    )

    messages = [HumanMessage(content="What is 3+3? Answer in one sentence.")]
    response = llm.invoke(messages)

    print(f"Response: {response.content}")

except Exception as e:
    print(f"❌ Test 2 failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
