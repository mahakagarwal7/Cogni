"""
Comprehensive test: Multiple topics with planning pattern detection
"""
import httpx
import asyncio

async def test_multiple_topics():
    async with httpx.AsyncClient() as client:
        topics = ["photosynthesis", "cell division", "neural networks", "quantum mechanics"]
        
        # Planning patterns to detect
        planning_indicators = [
            "then, i need", "so no", "no bullet", "four to five",
            "make it engaging", "also, check", "keep it flowing",
            "use examples like", "key point for", "also, mention",
            "should work", "just dive", "now, discuss", "let me structure",
            "need to explain", "avoid jargon", "use analogies"
        ]
        
        results = {"clean": 0, "issues": 0}
        
        for topic in topics:
            print(f"\n{topic.upper()}")
            print("-" * 50)
            
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": topic, "confusion_level": 3},
                timeout=30.0
            )
            
            data = response.json()
            explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
            
            if not explanation:
                print("  [SKIP] No explanation generated")
                continue
            
            # Check for planning patterns
            found = [p for p in planning_indicators if p in explanation.lower()]
            
            if found:
                print(f"  [ISSUE] Found: {found[0]}")
                results["issues"] += 1
            else:
                print(f"  [OK] Clean ({len(explanation)} chars)")
                results["clean"] += 1
        
        print("\n" + "=" * 50)
        print(f"SUMMARY: {results['clean']} clean, {results['issues']} issues")
        print("=" * 50)

asyncio.run(test_multiple_topics())
