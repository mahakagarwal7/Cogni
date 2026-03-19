#!/usr/bin/env python
"""Fresh test for Resonance LLM - forces clean module load"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force fresh imports
if 'app.engines.resonance_engine' in sys.modules:
    del sys.modules['app.engines.resonance_engine']
if 'app' in sys.modules:
    del sys.modules['app']

import asyncio
from app.engines.resonance_engine import ResonanceEngine

async def test():
    engine = ResonanceEngine()
    
    print("\n" + "="*70)
    print("TESTING RESONANCE LLM GENERATION (FRESH)")
    print("="*70 + "\n")
    
    test_cases = [
        ("rotational motion", "Physics - should use LLM"),
        ("photosynthesis", "Biology - should use LLM"),
        ("recursion", "CS - should use hardcoded"),
    ]
    
    for topic, description in test_cases:
        print(f"\nTopic: {topic}")
        print(f"Description: {description}")
        print("-" * 70)
        
        try:
            result = await engine.find_connections(topic)
            
            print(f"Demo Mode: {result['demo_mode']}")
            print(f"Connections ({len(result['hidden_connections'])}): ")
            for i, conn in enumerate(result['hidden_connections'][:3], 1):
                print(f"  {i}. {conn['topic']} ({conn['strength']:.2f})")
                print(f"     Reason: {conn['reason']}")
            
            print(f"\nInsight: {result['insight']}")
            
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
