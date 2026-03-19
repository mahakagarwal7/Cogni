#!/usr/bin/env python
"""Test the full archaeology pipeline with Hindsight + Groq"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.services.hindsight_service import hindsight_service

async def test_archaeology_pipeline():
    print("\n" + "="*60)
    print("TESTING FULL ARCHAEOLOGY PIPELINE")
    print("="*60 + "\n")
    
    topics = ["chemical equations", "recursion", "photosynthesis"]
    
    for topic in topics:
        print(f"\n📚 Topic: {topic}")
        print("-" * 60)
        
        # Call the full pipeline (async required)
        result = await hindsight_service.recall_temporal_archaeology(topic, 3)
        
        # Print the actual result structure
        print(f"Result keys: {result.keys()}")
        print(f"✓ Confidence: {result.get('confidence')}%")
        print(f"✓ Demo mode: {result.get('demo_mode', 'N/A')}")
        print(f"\n📖 Recommendation (Groq-Generated):\n{result.get('recommendation', 'ERROR')}")
        print()

if __name__ == "__main__":
    asyncio.run(test_archaeology_pipeline())
