#!/usr/bin/env python
"""Test the resonance engine with Hindsight"""

import asyncio
from app.engines.resonance_engine import ResonanceEngine

async def test_resonance():
    engine = ResonanceEngine()
    
    print("\n" + "="*70)
    print("TESTING RESONANCE ENGINE")
    print("="*70 + "\n")
    
    topics = ["recursion", "rotational motion", "photosynthesis", "matrices"]
    
    for topic in topics:
        print(f"Testing: {topic}")
        print("-" * 70)
        try:
            result = await engine.find_connections(topic)
            print(f"Feature: {result['feature']}")
            print(f"Demo Mode: {result['demo_mode']}")
            print(f"Insight: {result['insight']}")
            print(f"Connections:")
            for conn in result['hidden_connections']:
                print(f"  - {conn['topic']}: {conn['strength']} ({conn['reason']})")
            print()
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    asyncio.run(test_resonance())
