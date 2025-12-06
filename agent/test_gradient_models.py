#!/usr/bin/env python3
"""Test different Gradient models"""

import os
from dotenv import load_dotenv
from gradient import Gradient

load_dotenv()

client = Gradient(model_access_key=os.environ.get("DIGITALOCEAN_INFERENCE_KEY"))

models_to_test = [
    "openai-gpt-oss-120b",
    "llama3-70b-instruct",
    "llama3.3-70b-instruct",
    "mixtral-8x7b-instruct",
]

print("Testing Gradient Models...")
print("="*60)

for model in models_to_test:
    print(f"\n🧪 Testing: {model}")
    try:
        # Test with single user message (no system)
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Say 'hello' in one word."}
            ],
            model=model,
            max_tokens=20
        )

        print(f"Response object: {response}")
        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
            print(f"✅ WORKS! Response: {content}")
        else:
            print(f"⚠️ Empty response")

    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*60)
