#!/usr/bin/env python3
"""
Final comprehensive validation of all 5 cognitive features
"""
import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

async def main():
    print("=" * 70)
    print("COGNI BACKEND - FINAL VALIDATION TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    async with httpx.AsyncClient(timeout=30) as client:
        results = {
            "passed": [],
            "failed": [],
            "total": 0
        }
        
        # Test 1: Socratic (Teaching Questions)
        print("\n1️⃣  SOCRATIC ENGINE - Teaching Questions")
        print("-" * 70)
        try:
            response = await client.post(
                f"{BASE_URL}/socratic/ask?concept=inheritance&user_belief=it_makes_code_slower"
            )
            if response.status_code == 200:
                data = response.json()["data"]
                confidence = data.get("confidence")
                question = data.get("question", "")[:60] + "..."
                print(f"✅ Status: {response.status_code}")
                print(f"   Confidence: {confidence}")
                print(f"   Question: {question}")
                results["passed"].append("Socratic")
            else:
                print(f"❌ Failed with status {response.status_code}")
                results["failed"].append(f"Socratic ({response.status_code})")
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results["failed"].append(f"Socratic ({str(e)[:50]})")
        results["total"] += 1
        
        # Test 2: Shadow (Next Challenge Prediction)
        print("\n2️⃣  SHADOW ENGINE - Next Challenge Prediction")
        print("-" * 70)
        try:
            response = await client.get(f"{BASE_URL}/insights/shadow?topic=sorting")
            if response.status_code == 200:
                data = response.json()["data"]
                confidence = data.get("confidence")
                next_topic = data.get("next_challenge", "")[:50] + "..." if data.get("next_challenge") else "N/A"
                print(f"✅ Status: {response.status_code}")
                print(f"   Confidence: {confidence}")
                print(f"   Next Challenge: {next_topic}")
                results["passed"].append("Shadow")
            else:
                print(f"❌ Failed with status {response.status_code}")
                results["failed"].append(f"Shadow ({response.status_code})")
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results["failed"].append(f"Shadow ({str(e)[:50]})")
        results["total"] += 1
        
        # Test 3: Archaeology (Teaching Recommendations)
        print("\n3️⃣  ARCHAEOLOGY ENGINE - Teaching Recommendations")
        print("-" * 70)
        try:
            response = await client.get(
                f"{BASE_URL}/study/archaeology?topic=arrays&confusion_level=3"
            )
            if response.status_code == 200:
                data = response.json()["data"]
                confidence = data.get("confidence")
                recommendation = data.get("teaching_path", "")[:60] + "..." if data.get("teaching_path") else "N/A"
                print(f"✅ Status: {response.status_code}")
                print(f"   Confidence: {confidence}")
                print(f"   Teaching Path: {recommendation}")
                results["passed"].append("Archaeology")
            else:
                print(f"❌ Failed with status {response.status_code}")
                results["failed"].append(f"Archaeology ({response.status_code})")
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results["failed"].append(f"Archaeology ({str(e)[:50]})")
        results["total"] += 1
        
        # Test 4: Resonance (Topic Connections)
        print("\n4️⃣  RESONANCE ENGINE - Topic Connections")
        print("-" * 70)
        try:
            response = await client.get(f"{BASE_URL}/insights/resonance?topic=recursion")
            if response.status_code == 200:
                data = response.json()["data"]
                confidence = data.get("confidence")
                connections = data.get("connections", [])
                conn_str = ", ".join([c.get("topic", "?") for c in connections[:2]]) if connections else "N/A"
                print(f"✅ Status: {response.status_code}")
                print(f"   Confidence: {confidence}")
                print(f"   Connections: {conn_str}")
                results["passed"].append("Resonance")
            else:
                print(f"❌ Failed with status {response.status_code}")
                results["failed"].append(f"Resonance ({response.status_code})")
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results["failed"].append(f"Resonance ({str(e)[:50]})")
        results["total"] += 1
        
        # Test 5: Contagion (Community Insights) - Just Upgraded!
        print("\n5️⃣  CONTAGION ENGINE - Community Insights (🆕 UPGRADED)")
        print("-" * 70)
        try:
            response = await client.get(
                f"{BASE_URL}/insights/contagion?error_pattern=I+struggle+with+sorting+algorithms"
            )
            if response.status_code == 200:
                data = response.json()["data"]
                feature = data.get("feature")
                top_strategy = data.get("top_strategy", "N/A")
                success_rate = data.get("success_rate")
                num_strategies = len(data.get("additional_strategies", []))
                print(f"✅ Status: {response.status_code}")
                print(f"   Feature: {feature}")
                print(f"   Top Strategy: {top_strategy}")
                print(f"   Success Rate: {success_rate}")
                print(f"   Additional Strategies: {num_strategies}")
                results["passed"].append("Contagion")
            else:
                print(f"❌ Failed with status {response.status_code}")
                results["failed"].append(f"Contagion ({response.status_code})")
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results["failed"].append(f"Contagion ({str(e)[:50]})")
        results["total"] += 1
        
        # BONUS: Test Contagion with Multiple Topics
        print("\n🎯 BONUS - Contagion with Different Topics")
        print("-" * 70)
        test_topics = [
            "recursion base case",
            "graph traversal",
            "dynamic programming",
            "binary search"
        ]
        bonus_passed = 0
        for topic in test_topics:
            try:
                response = await client.get(
                    f"{BASE_URL}/insights/contagion?error_pattern={topic.replace(' ', '+')}"
                )
                if response.status_code == 200:
                    data = response.json()["data"]
                    strategy = data.get("top_strategy", "N/A")[:40] + "..."
                    print(f"   ✅ {topic}: {strategy}")
                    bonus_passed += 1
                else:
                    print(f"   ❌ {topic}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {topic}: Error")
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {len(results['passed'])}/{results['total']}")
        for feature in results["passed"]:
            print(f"   ✓ {feature}")
        
        if results["failed"]:
            print(f"\n❌ Failed: {len(results['failed'])}/{results['total']}")
            for error in results["failed"]:
                print(f"   ✗ {error}")
        
        print(f"\n🎁 Bonus Tests: {bonus_passed}/{len(test_topics)} topic variations")
        
        if len(results["passed"]) == results["total"]:
            print("\n" + "🎉" * 20)
            print("ALL TESTS PASSED - COGNI BACKEND FULLY OPERATIONAL!")
            print("🎉" * 20)
        else:
            print(f"\n⚠️  Some tests failed. Please review output above.")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
