"""
Check level 3's maybe
"""
import httpx
import asyncio

async def check():
    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": "Anti-addition reactions", "confusion_level": 3},
                timeout=30.0
            )
            
            result_data = response.json().get("data", {}).get("result", {})
            explanation = result_data.get("adaptive_explanation", "")
            
            if "maybe" in explanation.lower():
                print(f"Attempt {attempt+1}: Found maybe\n")
                sentences = explanation.split(". ")
                for i, sent in enumerate(sentences):
                    if "maybe" in sent.lower():
                        print(f"Sentence {i+1}: {sent}")
                break

asyncio.run(check())
