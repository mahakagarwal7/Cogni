#!/usr/bin/env python
"""Test all engines with user_id parameter."""
import asyncio
from app.engines.archaeology_engine import ArchaeologyEngine
from app.engines.shadow_engine import ShadowEngine
from app.engines.resonance_engine import ResonanceEngine
from app.engines.contagion_engine import ContagionEngine
from app.engines.socratic_engine import SocraticEngine

user_id = "testuser123"

async def test_all():
    print("\n" + "=" * 70)
    print("[TEST] All Engines with User ID Parameter")
    print("=" * 70 + "\n")
    
    # Test 1: Archaeology
    print("[1/5] Testing Archaeology Engine...")
    arch_engine = ArchaeologyEngine()
    result = await arch_engine.find_past_struggles("recursion", 3, 30, user_id)
    print(f"     ✓ Result feature: {result.get('feature')}")
    print(f"     ✓ Demo mode: {result.get('result', {}).get('demo_mode')}")
    print()
    
    # Test 2: Shadow
    print("[2/5] Testing Shadow Engine...")
    shadow_engine = ShadowEngine()
    result = await shadow_engine.get_prediction("arrays", user_id=user_id)
    print(f"     ✓ Result feature: {result.get('feature')}")
    print(f"     ✓ Demo mode: {result.get('demo_mode')}")
    print()
    
    # Test 3: Resonance
    print("[3/5] Testing Resonance Engine...")
    resonance_engine = ResonanceEngine()
    result = await resonance_engine.find_connections("sorting", user_id)
    print(f"     ✓ Result feature: {result.get('feature')}")
    print(f"     ✓ Demo mode: {result.get('demo_mode')}")
    print()
    
    # Test 4: Contagion
    print("[4/5] Testing Contagion Engine...")
    contagion_engine = ContagionEngine()
    result = await contagion_engine.get_community_insights("off-by-one errors", user_id)
    print(f"     ✓ Result feature: {result.get('feature')}")
    print(f"     ✓ Demo mode: {result.get('demo_mode')}")
    print()
    
    # Test 5: Socratic
    print("[5/5] Testing Socratic Engine...")
    socratic_engine = SocraticEngine()
    result = await socratic_engine.ask_socratic_question("scope", "global variables are faster", user_id)
    print(f"     ✓ Result feature: {result.get('feature')}")
    print(f"     ✓ Demo mode: {result.get('demo_mode')}")
    print()
    
    print("=" * 70)
    print("[SUCCESS] All engines tested successfully!")
    print("=" * 70)

asyncio.run(test_all())
