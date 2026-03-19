#!/usr/bin/env python3
"""
Test all 5 cognitive features after Contagion upgrade
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api"

async def test_all_features():
    async with httpx.AsyncClient() as client:
        results = {}
        
        # Test 1: Socratic
        print("Testing Socratic...")
        try:
            response = await client.post(
                f"{BASE_URL}/socratic/ask?concept=inheritance&user_belief=it_makes_code_slower"
            )
            data = response.json()["data"]
            results["socratic"] = {
                "confidence": data.get("confidence"),
                "status": "✓" if data.get("confidence") == 0.85 else "?"
            }
            print(f"  Socratic confidence: {data.get('confidence')} {results['socratic']['status']}")
        except Exception as e:
            print(f"  Socratic error: {e}")
            results["socratic"] = {"error": str(e)}
        
        # Test 2: Resonance
        print("Testing Resonance...")
        try:
            response = await client.get(f"{BASE_URL}/insights/resonance?topic=arrays")
            data = response.json()["data"]
            results["resonance"] = {
                "confidence": data.get("confidence"),
                "status": "✓" if data.get("confidence") == 0.9 else "?"
            }
            print(f"  Resonance confidence: {data.get('confidence')} {results['resonance']['status']}")
        except Exception as e:
            print(f"  Resonance error: {e}")
            results["resonance"] = {"error": str(e)}
        
        # Test 3: Shadow
        print("Testing Shadow...")
        try:
            response = await client.get(f"{BASE_URL}/insights/shadow?topic=sorting")
            data = response.json()["data"]
            results["shadow"] = {
                "confidence": data.get("confidence"),
                "status": "✓" if data.get("confidence") == 0.85 else "?"
            }
            print(f"  Shadow confidence: {data.get('confidence')} {results['shadow']['status']}")
        except Exception as e:
            print(f"  Shadow error: {e}")
            results["shadow"] = {"error": str(e)}
        
        # Test 4: Archaeology
        print("Testing Archaeology...")
        try:
            response = await client.get(
                f"{BASE_URL}/study/archaeology?topic=graphs&confusion_level=3"
            )
            data = response.json()["data"]
            results["archaeology"] = {
                "confidence": data.get("confidence"),
                "status": "✓" if data.get("confidence") == 0.75 else "?"
            }
            print(f"  Archaeology confidence: {data.get('confidence')} {results['archaeology']['status']}")
        except Exception as e:
            print(f"  Archaeology error: {e}")
            results["archaeology"] = {"error": str(e)}
        
        # Test 5: Contagion
        print("Testing Contagion...")
        try:
            response = await client.get(
                f"{BASE_URL}/insights/contagion?error_pattern=I+struggle+with+recursion+base+cases"
            )
            data = response.json()["data"]
            results["contagion"] = {
                "feature": data.get("feature"),
                "top_strategy": data.get("top_strategy"),
                "success_rate": data.get("success_rate"),
                "status": "✓" if data.get("feature") == "metacognitive_contagion" else "?"
            }
            print(f"  Contagion feature: {data.get('feature')} {results['contagion']['status']}")
            print(f"    Top strategy: {data.get('top_strategy')}")
            print(f"    Success rate: {data.get('success_rate')}")
        except Exception as e:
            print(f"  Contagion error: {e}")
            results["contagion"] = {"error": str(e)}
        
        # Test 6: Contagion with graphs topic
        print("\nTesting Contagion (graphs topic)...")
        try:
            response = await client.get(
                f"{BASE_URL}/insights/contagion?error_pattern=I+cannot+understand+graph+traversal+algorithms"
            )
            data = response.json()["data"]
            results["contagion_graphs"] = {
                "error_pattern": data.get("error_pattern"),
                "top_strategy": data.get("top_strategy"),
                "status": "✓"
            }
            print(f"  Pattern: {data.get('error_pattern')}")
            print(f"  Top strategy: {data.get('top_strategy')}")
        except Exception as e:
            print(f"  Contagion (graphs) error: {e}")
            results["contagion_graphs"] = {"error": str(e)}
        
        print("\n" + "="*60)
        print("SUMMARY:")
        print("="*60)
        for feature, result in results.items():
            status = result.get("status", "?")
            if "error" in result:
                print(f"❌ {feature}: {result['error']}")
            else:
                print(f"{status} {feature}: OK")
        
        return results

if __name__ == "__main__":
    asyncio.run(test_all_features())
