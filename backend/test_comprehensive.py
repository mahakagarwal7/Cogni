"""
Comprehensive test: Multiple topics across all 5 confusion levels
"""
import httpx
import asyncio

async def test_all_levels_all_topics():
    topics = ["photosynthesis", "water cycle", "drip irrigation", "mitochondria"]
    
    async with httpx.AsyncClient() as client:
        print("=" * 70)
        print("COMPREHENSIVE TEST: All Confusion Levels + Multiple Topics")
        print("=" * 70)
        
        results = {"clean": 0, "issues": 0}
        
        for topic in topics:
            print(f"\n{topic.upper()}")
            print("-" * 70)
            
            for level in [1, 2, 3, 4, 5]:
                response = await client.get(
                    "http://localhost:8000/api/study/archaeology",
                    params={"topic": topic, "confusion_level": level},
                    timeout=30.0
                )
                
                data = response.json()
                result = data.get("data", {}).get("result", {})
                explanation = result.get("adaptive_explanation", "")
                audience = result.get("explanation_audience", "unknown")
                
                if not explanation:
                    continue
                
                # Check for planning patterns
                planning_patterns = [
                    "from what i remember", "that's a good point", "that's important",
                    "one more thing", "there's also", "another thing", "and then",
                    "so the", "and that", "avoid using", "need to explain",
                    "use examples", "keep it flowing", "four to five"
                ]
                
                found = [p for p in planning_patterns if p in explanation.lower()]
                
                if found:
                    print(f"  L{level} ({audience:16}): [ISSUE] {found[0]}")
                    results["issues"] += 1
                else:
                    print(f"  L{level} ({audience:16}): [OK] {len(explanation):4} chars")
                    results["clean"] += 1
        
        print("\n" + "=" * 70)
        print(f"TOTAL: {results['clean']} clean, {results['issues']} issues")
        print("=" * 70)

asyncio.run(test_all_levels_all_topics())
