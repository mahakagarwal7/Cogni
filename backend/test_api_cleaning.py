"""
Integration test: Call the /api/study/archaeology endpoint
and verify adaptive explanations are clean (no thinking content)
"""
import httpx
import json
import asyncio

API_URL = "http://localhost:8000"

async def test_adaptive_explanations():
    """Test all confusion levels for clean explanations"""
    
    async with httpx.AsyncClient() as client:
        topic = "Anti-addition reactions"
        
        print("=" * 70)
        print("ADAPTIVE EXPLANATION CLEANING - API INTEGRATION TEST")
        print("=" * 70)
        
        for confusion_level in [1, 2, 3, 4, 5]:
            print(f"\n[Testing] Confusion Level {confusion_level}/5")
            print("-" * 70)
            
            try:
                response = await client.get(
                    f"{API_URL}/api/study/archaeology",
                    params={
                        "topic": topic,
                        "confusion_level": confusion_level
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"  [ERROR] Status {response.status_code}")
                    print(f"  {response.text}")
                    continue
                
                data = response.json()
                
                # Check for adaptive_explanation field in nested result
                result_data = data.get("data", {}).get("result", {})
                if "adaptive_explanation" not in result_data:
                    print("  [SKIP] No adaptive_explanation in response")
                    continue
                
                explanation = result_data["adaptive_explanation"]
                
                # Check for thinking patterns
                thinking_patterns = [
                    "wait,", "hmm,", "maybe", "let me", 
                    "but wait", "but how", "i think",
                    "Actually,", "hmm,", "i should",
                    "i'm not sure", "need to be careful"
                ]
                
                found_thinking = []
                for pattern in thinking_patterns:
                    if pattern.lower() in explanation.lower():
                        found_thinking.append(pattern)
                
                # Show result
                if found_thinking:
                    print(f"  [ISSUE] Found thinking patterns: {found_thinking}")
                    # Show first part of explanation for debugging
                    print(f"  Preview: {explanation[:200]}...")
                else:
                    print(f"  [OK] Clean explanation ({len(explanation)} chars)")
                    print(f"  Audience: {result_data.get('explanation_audience', 'N/A')}")
                    # Show first part
                    print(f"  Start: {explanation[:150]}...")
                
            except Exception as e:
                print(f"  [ERROR] {type(e).__name__}: {str(e)[:100]}")
        
        print("\n" + "=" * 70)
        print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_adaptive_explanations())
