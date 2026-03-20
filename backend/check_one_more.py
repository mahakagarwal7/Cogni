"""
Check the final remaining pattern
"""
import httpx
import asyncio

async def check():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "drip irrigation", "confusion_level": 5},
            timeout=30.0
        )
        data = response.json()
        explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
        
        print("=" * 70)
        print("DRIP IRRIGATION LEVEL 5 (5-year-old)")
        print("=" * 70)
        print(explanation)
        print("=" * 70)

asyncio.run(check())
