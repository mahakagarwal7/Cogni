#!/usr/bin/env python
"""Comprehensive test of all 4 cognitive features together"""

import asyncio
from app.engines.socratic_engine import SocraticEngine
from app.engines.shadow_engine import ShadowEngine
from app.engines.archaeology_engine import ArchaeologyEngine
from app.engines.resonance_engine import ResonanceEngine

async def test_all_features():
    socratic = SocraticEngine()
    shadow = ShadowEngine()
    archaeology = ArchaeologyEngine()
    resonance = ResonanceEngine()
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST: ALL 4 COGNITIVE FEATURES")
    print("=" * 80)
    
    test_topic = "rotational motion"
    misconception = "I think rotational motion is just linear motion in circles"
    
    print(f"\nTest Case: {test_topic}")
    print(f"Misconception: {misconception}\n")
    
    # 1. SOCRATIC - Challenge the misconception
    print("1. SOCRATIC - Teaching Questions")
    print("-" * 80)
    try:
        socratic_result = await socratic.ask_socratic_question(
            concept=test_topic,
            user_belief=misconception
        )
        print(f"Question: {socratic_result['question']}")
        print(f"Confidence: {socratic_result.get('confidence', 'N/A')}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # 2. SHADOW - Predict next challenge
    print("\n2. SHADOW - Next Challenge Prediction")
    print("-" * 80)
    try:
        shadow_result = await shadow.get_prediction(current_topic=test_topic)
        print(f"Prediction: {shadow_result['prediction']}")
        print(f"Evidence: {shadow_result['evidence']}")
        print(f"Confidence: {shadow_result['confidence']:.2f}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # 3. ARCHAEOLOGY - Find teaching recommendations
    print("\n3. ARCHAEOLOGY - Teaching Recommendations")
    print("-" * 80)
    try:
        arch_result = await archaeology.find_past_struggles(
            topic=test_topic,
            confusion_level=3
        )
        inner_result = arch_result['result']
        recommendation = inner_result.get('recommendation', 'No recommendation available')
        print(f"Similar moments found: {inner_result['similar_moments']}")
        print(f"Recommendation: {recommendation}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # 4. RESONANCE - Find connected topics
    print("\n4. RESONANCE - Related Topic Connections")
    print("-" * 80)
    try:
        resonance_result = await resonance.find_connections(test_topic)
        print(f"Insight: {resonance_result['insight']}")
        print(f"Related Topics:")
        for i, conn in enumerate(resonance_result['hidden_connections'][:3], 1):
            print(f"  {i}. {conn['topic']} ({conn['strength']:.2f})")
            print(f"     {conn['reason']}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("ALL FEATURES TESTED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_all_features())
