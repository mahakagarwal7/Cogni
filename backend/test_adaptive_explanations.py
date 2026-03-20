"""
Test the adaptive explanation feature in archaeology engine
"""

import asyncio
from app.engines.archaeology_engine import ArchaeologyEngine
from app.services.hindsight_service import hindsight_service

async def test_adaptive_explanations():
    """Test that adaptive explanations are generated for all confusion levels"""
    engine = ArchaeologyEngine(hindsight_service)
    
    topic = "recursion"
    
    print("\n" + "="*80)
    print("ADAPTIVE EXPLANATION FEATURE TEST")
    print("="*80)
    
    test_cases = [
        {"level": 1, "name": "Undergraduate"},
        {"level": 2, "name": "JEE/NEET"},
        {"level": 3, "name": "High School"},
        {"level": 4, "name": "Middle School"},
        {"level": 5, "name": "5-Year-Old"},
    ]
    
    for test in test_cases:
        try:
            result = await engine.find_past_struggles(
                topic=topic,
                confusion_level=test["level"],
                days=30
            )
            
            explanation = result.get("result", {}).get("adaptive_explanation", "")
            audience = result.get("result", {}).get("explanation_audience", "")
            
            print(f"\n[Level {test['level']}] {test['name']}")
            print(f"  Audience: {audience}")
            
            if explanation:
                # Count paragraphs (separated by double newlines)
                paragraphs = [p.strip() for p in explanation.split("\n\n") if p.strip()]
                print(f"  Paragraphs: {len(paragraphs)}")
                print(f"  Length: {len(explanation)} chars")
                
                # Check for issues
                issues = []
                if "<think>" in explanation or "</think>" in explanation:
                    issues.append("Contains thinking tags")
                if "let me explain" in explanation.lower():
                    issues.append("Contains meta-phrase 'let me explain'")
                if "i'll explain" in explanation.lower():
                    issues.append("Contains meta-phrase 'i'll explain'")
                
                if issues:
                    print(f"  Issues: {issues}")
                else:
                    print(f"  Status: CLEAN")
                
                # Show first 150 chars
                preview = explanation[:150].replace("\n", " ")
                print(f"  Preview: {preview}...")
            else:
                print(f"  Status: NO EXPLANATION GENERATED")
        
        except Exception as e:
            print(f"\n[Level {test['level']}] ERROR: {str(e)[:80]}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_adaptive_explanations())
