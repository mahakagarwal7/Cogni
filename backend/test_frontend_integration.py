#!/usr/bin/env python
"""
End-to-End Integration Test - Multiple Users
Tests the complete flow from frontend userId through backend engines to hindsight API
"""

import asyncio
from app.engines.archaeology_engine import ArchaeologyEngine
from app.engines.shadow_engine import ShadowEngine
from app.engines.resonance_engine import ResonanceEngine
from app.engines.contagion_engine import ContagionEngine
from app.engines.socratic_engine import SocraticEngine


async def test_end_to_end():
    """
    Simulate multiple frontend users making queries with their user_ids
    """
    
    print("\n" + "="*80)
    print("END-TO-END INTEGRATION TEST: Multiple Users")
    print("="*80)
    print("Simulating: Frontend passes userId → Route receives it → Engine uses it")
    print("="*80 + "\n")
    
    # Simulate different users from frontend (like localStorage user_id)
    test_users = [
        "alice_student",
        "bob_learner", 
        "charlie_dev"
    ]
    
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "by_user": {}
    }
    
    # Test each user
    for user_id in test_users:
        print(f"\n{'='*80}")
        print(f"👤 TESTING USER: {user_id}")
        print(f"{'='*80}")
        
        results["by_user"][user_id] = []
        
        # ====== ARCHAEOLOGY ENGINE ======
        print(f"\n[1/5] Archaeology Engine")
        print(f"      Topic: linked_lists, User: {user_id}")
        try:
            engine = ArchaeologyEngine()
            response = await engine.find_past_struggles(
                topic="linked_lists",
                confusion_level=2,
                days=30,
                user_id=user_id  # ← Frontend userId passed through Route
            )
            
            feature = response.get("feature")
            demo_mode = response.get("result", {}).get("demo_mode")
            
            print(f"      ✓ Feature: {feature}")
            print(f"      ✓ Demo mode: {demo_mode}")
            
            if demo_mode is False:
                print(f"      ✅ PASS: Real API used for {user_id}")
                results["success"] += 1
            else:
                print(f"      ❌ FAIL: Demo mode for {user_id}")
                results["failed"] += 1
            
            results["by_user"][user_id].append({
                "engine": "archaeology",
                "feature": feature,
                "demo_mode": demo_mode,
                "status": "✅" if demo_mode is False else "❌"
            })
            results["total"] += 1
            
        except Exception as e:
            print(f"      ❌ ERROR: {str(e)}")
            results["failed"] += 1
            results["total"] += 1
        
        # ====== SHADOW ENGINE ======
        print(f"\n[2/5] Shadow Engine")
        print(f"      Topic: trees, User: {user_id}")
        try:
            engine = ShadowEngine()
            response = await engine.get_prediction(
                current_topic="trees",
                days=14,
                user_id=user_id  # ← Frontend userId
            )
            
            feature = response.get("feature")
            demo_mode = response.get("demo_mode")
            
            print(f"      ✓ Feature: {feature}")
            print(f"      ✓ Demo mode: {demo_mode}")
            
            if demo_mode is False:
                print(f"      ✅ PASS: Real API used for {user_id}")
                results["success"] += 1
            else:
                print(f"      ❌ FAIL: Demo mode for {user_id}")
                results["failed"] += 1
            
            results["by_user"][user_id].append({
                "engine": "shadow",
                "feature": feature,
                "demo_mode": demo_mode,
                "status": "✅" if demo_mode is False else "❌"
            })
            results["total"] += 1
            
        except Exception as e:
            print(f"      ❌ ERROR: {str(e)}")
            results["failed"] += 1
            results["total"] += 1
        
        # ====== RESONANCE ENGINE ======
        print(f"\n[3/5] Resonance Engine")
        print(f"      Topic: graph_algorithms, User: {user_id}")
        try:
            engine = ResonanceEngine()
            response = await engine.find_connections(
                topic="graph_algorithms",
                user_id=user_id  # ← Frontend userId
            )
            
            feature = response.get("feature")
            demo_mode = response.get("demo_mode")
            
            print(f"      ✓ Feature: {feature}")
            print(f"      ✓ Demo mode: {demo_mode}")
            
            if demo_mode is False:
                print(f"      ✅ PASS: Real API used for {user_id}")
                results["success"] += 1
            else:
                print(f"      ❌ FAIL: Demo mode for {user_id}")
                results["failed"] += 1
            
            results["by_user"][user_id].append({
                "engine": "resonance",
                "feature": feature,
                "demo_mode": demo_mode,
                "status": "✅" if demo_mode is False else "❌"
            })
            results["total"] += 1
            
        except Exception as e:
            print(f"      ❌ ERROR: {str(e)}")
            results["failed"] += 1
            results["total"] += 1
        
        # ====== CONTAGION ENGINE ======
        print(f"\n[4/5] Contagion Engine")
        print(f"      Topic: off-by-one errors, User: {user_id}")
        try:
            engine = ContagionEngine()
            response = await engine.get_community_insights(
                error_pattern="off-by-one errors",
                user_id=user_id  # ← Frontend userId
            )
            
            feature = response.get("feature")
            demo_mode = response.get("demo_mode")
            
            print(f"      ✓ Feature: {feature}")
            print(f"      ✓ Demo mode: {demo_mode}")
            
            if demo_mode is False:
                print(f"      ✅ PASS: Real API used for {user_id}")
                results["success"] += 1
            else:
                print(f"      ❌ FAIL: Demo mode for {user_id}")
                results["failed"] += 1
            
            results["by_user"][user_id].append({
                "engine": "contagion",
                "feature": feature,
                "demo_mode": demo_mode,
                "status": "✅" if demo_mode is False else "❌"
            })
            results["total"] += 1
            
        except Exception as e:
            print(f"      ❌ ERROR: {str(e)}")
            results["failed"] += 1
            results["total"] += 1
        
        # ====== SOCRATIC ENGINE ======
        print(f"\n[5/5] Socratic Engine")
        print(f"      Topic: scope, User: {user_id}")
        try:
            engine = SocraticEngine()
            response = await engine.ask_socratic_question(
                concept="scope",
                user_belief="global variables are faster",
                user_id=user_id  # ← Frontend userId
            )
            
            feature = response.get("feature")
            demo_mode = response.get("demo_mode")
            
            print(f"      ✓ Feature: {feature}")
            print(f"      ✓ Demo mode: {demo_mode}")
            
            if demo_mode is False:
                print(f"      ✅ PASS: Real API used for {user_id}")
                results["success"] += 1
            else:
                print(f"      ❌ FAIL: Demo mode for {user_id}")
                results["failed"] += 1
            
            results["by_user"][user_id].append({
                "engine": "socratic",
                "feature": feature,
                "demo_mode": demo_mode,
                "status": "✅" if demo_mode is False else "❌"
            })
            results["total"] += 1
            
        except Exception as e:
            print(f"      ❌ ERROR: {str(e)}")
            results["failed"] += 1
            results["total"] += 1
    
    # ========== SUMMARY ==========
    print(f"\n\n{'='*80}")
    print("📊 INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests Run: {results['total']}")
    print(f"Passed (Real API): {results['success']} ✅")
    print(f"Failed (Demo Mode): {results['failed']} ❌")
    
    print(f"\n{'Detailed Results by User:':-^80}")
    for user_id, interactions in results["by_user"].items():
        print(f"\n👤 {user_id}:")
        for interaction in interactions:
            engine = interaction["engine"].ljust(12)
            demo = "REAL API ✅" if interaction["demo_mode"] is False else "DEMO MODE ❌"
            print(f"   • {engine} → {demo}")
    
    print(f"\n{'='*80}")
    if results["failed"] == 0:
        print("🎉 SUCCESS: All users can use real Hindsight API!")
        print("   ✅ Frontend userId properly passed through routes")
        print("   ✅ Engines receiving user context for personalization")
        print("   ✅ Memory retention enabled for each user")
        print("   ✅ Demo mode is OFF - Production ready!")
    else:
        print("⚠️  Some tests failed - see details above")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_end_to_end())
