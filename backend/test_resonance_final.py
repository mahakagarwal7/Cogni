#!/usr/bin/env python
"""Final validation test for Resonance with enhanced reasons"""

import asyncio
from app.engines.resonance_engine import ResonanceEngine

async def test():
    engine = ResonanceEngine()
    
    test_cases = [
        "rotational motion",
        "photosynthesis", 
        "linear regression",
        "recursion"
    ]
    
    for topic in test_cases:
        result = await engine.find_connections(topic)
        print(f"\n{topic.upper()}")
        print(f"  Demo: {result['demo_mode']}")
        for i, conn in enumerate(result['hidden_connections'][:3], 1):
            print(f"  {i}. {conn['topic']} ({conn['strength']:.2f})")
            print(f"     > {conn['reason']}")

if __name__ == "__main__":
    asyncio.run(test())
