"""
Test to find remaining thinking patterns in level-based explanations
"""
import httpx
import asyncio

async def test_drip_irrigation_levels():
    async with httpx.AsyncClient() as client:
        print("=" * 70)
        print("DRIP IRRIGATION - LEVEL-BASED EXPLANATION TEST")
        print("=" * 70)
        
        for level in [1, 2, 3, 4, 5]:
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": "drip irrigation", "confusion_level": level},
                timeout=30.0
            )
            
            data = response.json()
            result = data.get("data", {}).get("result", {})
            explanation = result.get("adaptive_explanation", "")
            audience = result.get("explanation_audience", "unknown")
            
            if not explanation:
                print(f"\nLevel {level} ({audience}): [SKIP] No explanation")
                continue
            
            # Comprehensive list of thinking/planning patterns that should be cleaned
            thinking_indicators = [
                "from what i", "from what i remember",  # Recollection thinking
                "that's a good point", "that's important",  # Retrospective evaluation
                "so the", "and that", "and then",  # Transition words indicating planning
                "another thing", "another angle",  # Enumeration from planning
                "there's also", "there's", # Thinking and enumeration
                "one more thing",
            ]
            
            found = []
            for indicator in thinking_indicators:
                if indicator in explanation.lower():
                    found.append(indicator)
            
            print(f"\nLevel {level} ({audience}):")
            print(f"  Length: {len(explanation)} chars")
            
            if found:
                print(f"  [ISSUE] Found patterns: {found}")
                # Show sentences with these patterns
                sentences = explanation.split(". ")
                for sent in sentences[:5]:  # First 5 sentences
                    for pat in found:
                        if pat in sent.lower():
                            print(f"    >> {sent[:100]}...")
                            break
            else:
                print(f"  [OK] Clean")
                print(f"       Start: {explanation[:120]}...")

asyncio.run(test_drip_irrigation_levels())
