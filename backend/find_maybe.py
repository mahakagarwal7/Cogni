"""
Find the maybe in level 4
"""
import httpx
import asyncio

async def find():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "Anti-addition reactions", "confusion_level": 4},
            timeout=30.0
        )
        
        result_data = response.json().get("data", {}).get("result", {})
        explanation = result_data.get("adaptive_explanation", "")
        
        if "maybe" in explanation.lower():
            sentences = explanation.split(". ")
            for i, sent in enumerate(sentences):
                if "maybe" in sent.lower():
                    print(f"Sentence {i+1}: {sent}")

asyncio.run(find())
