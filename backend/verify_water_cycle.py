"""
Detailed water cycle verification - show full clean explanation
"""
import httpx
import asyncio

async def verify_water_cycle():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "water cycle", "confusion_level": 3},
            timeout=30.0
        )
        
        data = response.json()
        result = data.get("data", {}).get("result", {})
        explanation = result.get("adaptive_explanation", "")
        audience = result.get("explanation_audience", "unknown")
        
        print("=" * 70)
        print("WATER CYCLE - CLEAN EXPLANATION")
        print("=" * 70)
        print(f"\nAudience: {audience}")
        print(f"Length: {len(explanation)} chars")
        print("\nFull Explanation:")
        print("-" * 70)
        print(explanation)
        print("-" * 70)
        
        # Verify it has technical content
        has_technical = any(term in explanation.lower() for term in [
            "evaporation", "condensation", "precipitation", "water",
            "clouds", "temperature", "heat", "cycle", "transport",
            "atmosphere", "energy", "phase"
        ])
        
        print(f"\nHas technical content: {has_technical}")
        print(f"Is educational: {len(explanation) > 100 and has_technical}")

asyncio.run(verify_water_cycle())
