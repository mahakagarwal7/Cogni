"""
Check if remaining patterns are thinking or legitimate content
"""
import httpx
import asyncio

async def check_pattern_context():
    async with httpx.AsyncClient() as client:
        # Check the photosynthesis level 3 that has "so the"
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "photosynthesis", "confusion_level": 3},
            timeout=30.0
        )
        
        data = response.json()
        explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
        
        print("=" * 70)
        print("PHOTOSYNTHESIS LEVEL 3 (high_school) - Contains 'so the'")
        print("=" * 70)
        print(explanation)
        print("\n" + "=" * 70)
        
        # Check water cycle level 4 with "use examples"
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "water cycle", "confusion_level": 4},
            timeout=30.0
        )
        
        data = response.json()
        explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
        
        print("\nWATER CYCLE LEVEL 4 (middle_school) - Contains 'use examples'")
        print("=" * 70)
        print(explanation)
        print("\n" + "=" * 70)

asyncio.run(check_pattern_context())
