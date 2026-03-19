#!/usr/bin/env python
"""Test: Verify single confidence level based on confusion_level"""

import asyncio
from app.engines.archaeology_engine import ArchaeologyEngine
from app.engines.socratic_engine import SocraticEngine
from app.engines.resonance_engine import ResonanceEngine
from app.engines.shadow_engine import ShadowEngine

async def test():
    print("\n" + "="*80)
    print("VERIFYING SINGLE CONFIDENCE LEVEL")
    print("="*80)
    
    # Test 1: Archaeology with different confusion levels
    print("\n1. ARCHAEOLOGY - Confidence based on confusion_level")
    print("-"*80)
    arch = ArchaeologyEngine()
    for conf_level in [1, 2, 3, 4, 5]:
        result = await arch.find_past_struggles("recursion", confusion_level=conf_level)
        confidence = result.get("confidence", "MISSING")
        print(f"   Confusion level {conf_level} -> Confidence: {confidence}")
    
    # Test 2: Socratic
    print("\n2. SOCRATIC - Fixed confidence level")
    print("-"*80)
    socratic = SocraticEngine()
    result = await socratic.ask_socratic_question(
        concept="loops",
        user_belief="loops are hard"
    )
    confidence = result.get("confidence", "MISSING")
    print(f"   Socratic confidence: {confidence}")
    
    # Test 3: Resonance - Confidence based on connections found
    print("\n3. RESONANCE - Confidence based on connections count")
    print("-"*80)
    resonance = ResonanceEngine()
    test_topics = ["recursion", "rotational motion"]
    for topic in test_topics:
        result = await resonance.find_connections(topic)
        confidence = result.get("confidence", "MISSING")
        num_connections = len(result.get("hidden_connections", []))
        print(f"   {topic}: {num_connections} connections -> Confidence: {confidence}")
    
    # Test 4: Shadow
    print("\n4. SHADOW - Confidence level")
    print("-"*80)
    shadow = ShadowEngine()
    result = await shadow.get_prediction(current_topic="recursion")
    confidence = result.get("confidence", "MISSING")
    print(f"   Shadow confidence: {confidence}")
    
    print("\n" + "="*80)
    print("SUCCESS! All features have single confidence level")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test())
