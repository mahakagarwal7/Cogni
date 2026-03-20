"""
Capture detailed view of a potentially problematic level
"""
import httpx
import asyncio

async def capture():
    async with httpx.AsyncClient() as client:
        # Try level 1 a few times to see if we can get the maybe variant
        for attempt in range(3):
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": "Anti-addition reactions", "confusion_level": 1},
                timeout=30.0
            )
            
            result_data = response.json().get("data", {}).get("result", {})
            explanation = result_data.get("adaptive_explanation", "")
            
            if "maybe" in explanation.lower():
                print(f"\nAttempt {attempt+1}: Found maybe")
                print("=" * 70)
                print(explanation)
                print("\n" + "=" * 70)
                sentences = explanation.split(". ")
                for i, sent in enumerate(sentences):
                    if "maybe" in sent.lower():
                        print(f"Sentence {i+1}: {sent}")
                break
            else:
                print(f"Attempt {attempt+1}: No maybe found")

asyncio.run(capture())
