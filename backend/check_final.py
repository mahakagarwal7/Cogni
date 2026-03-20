"""
Check the final two patterns
"""
import httpx
import asyncio

async def check_final():
    async with httpx.AsyncClient() as client:
        # Water cycle level 4 with "and then"
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "water cycle", "confusion_level": 4},
            timeout=30.0
        )
        data = response.json()
        explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
        
        print("=" * 70)
        print("WATER CYCLE LEVEL 4 - 'and then' pattern")
        print("=" * 70)
        print(explanation)
        print("\n" + "=" * 70)
        
        # Mitochondria level 5 with "so the"
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "mitochondria", "confusion_level": 5},
            timeout=30.0
        )
        data = response.json()
        explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
        
        print("\nMITOCHONDRIA LEVEL 5 - 'so the' pattern")
        print("=" * 70)
        print(explanation)
        print("=" * 70)

asyncio.run(check_final())
