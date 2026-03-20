"""
Test water cycle adaptive explanation for planning content
"""
import httpx
import asyncio

async def test_water_cycle():
    async with httpx.AsyncClient() as client:
        print("=" * 70)
        print("WATER CYCLE - ADAPTIVE EXPLANATION TEST")
        print("=" * 70)
        
        for level in [2, 3, 4]:
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": "water cycle", "confusion_level": level},
                timeout=30.0
            )
            
            data = response.json()
            result = data.get("data", {}).get("result", {})
            explanation = result.get("adaptive_explanation", "")
            
            print(f"\nLevel {level}:")
            print("-" * 70)
            
            # Check for planning patterns
            planning_patterns = [
                "then, i need", "so no", "no bullet", "four to five",
                "make it engaging", "also, check", "keep it flowing",
                "use examples like", "key point for", "also, mention",
                "should work", "just dive"
            ]
            
            found = []
            for pattern in planning_patterns:
                if pattern in explanation.lower():
                    found.append(pattern)
            
            if found:
                print(f"  [ISSUE] Found planning patterns: {found}")
                sentences = explanation.split(". ")
                for sent in sentences:
                    for p in found:
                        if p in sent.lower():
                            print(f"    >> {sent[:80]}...")
                            break
            else:
                print(f"  [OK] Clean explanation ({len(explanation)} chars)")
                print(f"  Start: {explanation[:150]}...")

asyncio.run(test_water_cycle())
