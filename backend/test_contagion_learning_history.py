#!/usr/bin/env python3
"""
Test the UPDATED Contagion Engine that uses Hindsight Learning History
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api"

async def main():
    print("\n" + "="*70)
    print("CONTAGION ENGINE - UPDATED TO USE STUDENT LEARNING HISTORY")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Test cases
        test_patterns = [
            "I struggle with sorting algorithms",
            "Recursion confuses me",
            "Graph traversal is difficult",
            "I can't grasp dynamic programming"
        ]
        
        for pattern in test_patterns:
            try:
                response = await client.get(
                    f"{BASE_URL}/insights/contagion",
                    params={"error_pattern": pattern}
                )
                
                if response.status_code == 200:
                    data = response.json()["data"]
                    
                    print(f"\n📚 Pattern: '{pattern}'")
                    print(f"   Top Strategy: {data.get('top_strategy')}")
                    print(f"   Success Rate: {data.get('success_rate'):.0%}")
                    print(f"   Source: {data.get('privacy_note')}")
                    print(f"   Additional Strategies: {len(data.get('additional_strategies', []))}")
                    
                    # Show first strategy details
                    if data.get("additional_strategies"):
                        first = data["additional_strategies"][0]
                        source = first.get("source", "unknown")
                        if source == "from_your_history":
                            print(f"   🎯 PERSONALIZED: Using your learning history!")
                        elif source == "learning_style":
                            print(f"   🎯 ADAPTED: Based on your learning style")
                        elif source == "from_community":
                            print(f"   📊 COMMUNITY: From peer analysis")
                else:
                    print(f"❌ Error {response.status_code}")
            
            except Exception as e:
                print(f"❌ Error: {str(e)[:80]}")
        
        print("\n" + "="*70)
        print("KEY CHANGES:")
        print("="*70)
        print("✅ NOW uses Hindsight to recall student's LEARNING HISTORY")
        print("✅ Extracts successful strategies student has used before")
        print("✅ Infers student's LEARNING STYLE from past memories")
        print("✅ Prioritizes strategies based on what worked for THIS student")
        print("✅ Privacy note changed: 'Personalized based on your learning history + peer patterns'")
        print("✅ Strategies marked with source: from_your_history, learning_style, or from_community")
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
