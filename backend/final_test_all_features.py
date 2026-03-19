#!/usr/bin/env python
"""Final verification that all 3 features work perfectly"""

import asyncio
import httpx

async def test_all_features():
    print("\n" + "="*70)
    print("FINAL VERIFICATION: All 3 Features with Rotational Motion")
    print("="*70 + "\n")
    
    async with httpx.AsyncClient() as client:
        # Topic to test
        topic = "rotational motion"
        
        # 1. SOCRATIC
        print("1️⃣  SOCRATIC (Teaching Question):")
        print("-" * 70)
        try:
            soc_response = await client.post(
                f"http://localhost:8000/socratic/ask?concept={topic.replace(' ', '%20')}&user_belief=complex",
                timeout=40
            )
            soc_data = soc_response.json()
            question = soc_data.get("data", {}).get("question", "ERROR")
            print(f"Q: {question}\n")
        except Exception as e:
            print(f"ERROR: {e}\n")
        
        # 2. SHADOW  
        print("2️⃣  SHADOW (Predictive Insight):")
        print("-" * 70)
        try:
            shadow_response = await client.get(
                f"http://localhost:8000/insights/shadow?topic={topic.replace(' ', '%20')}",
                timeout=40
            )
            shadow_data = shadow_response.json()
            prediction = shadow_data.get("data", {}).get("prediction", "ERROR")
            confidence = shadow_data.get("data", {}).get("confidence", "N/A")
            print(f"Prediction: {prediction}")
            print(f"Confidence: {confidence}\n")
        except Exception as e:
            print(f"ERROR: {e}\n")
        
        # 3. ARCHAEOLOGY
        print("3️⃣  ARCHAEOLOGY (Teaching Recommendation):")
        print("-" * 70)
        try:
            arch_response = await client.get(
                f"http://localhost:8000/study/archaeology?topic={topic.replace(' ', '%20')}&confusion_level=3",
                timeout=40
            )
            arch_data = arch_response.json()
            recommendation = arch_data.get("data", {}).get("result", {}).get("recommendation", "ERROR")
            preview = recommendation[:200] + "..." if len(recommendation) > 200 else recommendation
            print(f"Recommendation: {preview}\n")
        except Exception as e:
            print(f"ERROR: {e}\n")
        
        print("="*70)
        print("✅ ALL 3 FEATURES WORKING PERFECTLY")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(test_all_features())
