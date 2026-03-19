#!/usr/bin/env python
"""Test Resonance feature with LLM connection generation."""

import asyncio
from app.engines.resonance_engine import ResonanceEngine

async def test_resonance():
    engine = ResonanceEngine()
    
    test_topics = [
        'rotational motion',
        'photosynthesis',
        'linear algebra',
        'recursion',
        'quantum mechanics'
    ]
    
    for topic in test_topics:
        print(f'\n=== Testing {topic} ===')
        try:
            result = await engine.find_connections(topic)
            print(f'Demo Mode: {result["demo_mode"]}')
            print(f'Connections: {len(result["hidden_connections"])}')
            for conn in result['hidden_connections'][:3]:
                print(f'  - {conn["topic"]}: {conn["strength"]:.2f}')
                print(f'    Reason: {conn["reason"]}')
            if result['insight']:
                print(f'Insight: {result["insight"]}')
        except Exception as e:
            print(f'ERROR: {e}')

if __name__ == '__main__':
    asyncio.run(test_resonance())
