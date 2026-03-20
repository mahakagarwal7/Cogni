"""
Test aggressive thinking content removal for the anti-addition example
"""

from app.engines.archaeology_engine import ArchaeologyEngine
from app.services.hindsight_service import hindsight_service

# The problematic response the user showed
PROBLEMATIC_RESPONSE = """"anti addition" for JEE/NEET aspirants. Let me start by recalling what I know. Anti addition is a type of reaction in organic chemistry where two substituents add to opposite sides of a double bond. Wait, right, like in the case of bromine adding to an alkene. But how exactly does that work?

First, I should define anti addition clearly. It's the opposite of syn addition, where both groups add to the same side. Maybe I can compare them using examples. Like, bromine water with an alkene gives anti addition, while maybe HBr with peroxides gives syn? No, wait, HBr with peroxides is anti-Markovnikov but still anti addition? Hmm, maybe I should stick to the bromine example.

Let me think about the mechanism. When bromine adds to an alkene, it forms a bromonium ion intermediate. The bromide ion then attacks from the opposite side, leading to anti addition. That's a key point. So the spatial arrangement is important here. The molecule can't rotate once the double bond is broken, so the attack has to happen from the opposite face.

Wait, another example could be the addition of hydrogen halides in the presence of peroxides. But I'm not sure if that's anti addition. Maybe better to focus on the bromine example. Also, maybe mention that anti addition is common in halogen addition reactions. Oh, and the diastereomers formed can be a result of this. For instance, if the alkene is cis or trans, the product's stereochemistry will differ.

I should also mention the anti addition in the context of hydroboration-oxidation, but wait, hydroboration is syn addition. So maybe avoid that. Stick to bromine addition. Also, maybe contrast with syn addition in another reaction. For example, in hydration using H2O and H2SO4, the addition is anti-Markovnikov but syn? No, wait, acid-catalyzed hydration is Markovnikov and syn? Or is it anti? I need to be careful here. Maybe it's better to use the bromine addition as the main example and compare with another reaction where syn addition occurs, like hydrogenation with H2 and a catalyst.

Another point to consider is the use of the term "anti" in the context of stereochemistry. It refers to the direction from which the reagents approach the molecule. So, when you have a planar molecule like an alkene, adding two groups from opposite sides gives anti addition. This is different from syn addition where both groups add to the same face.

I need to make sure the explanation is clear and uses examples that are familiar to JEE/NEET students. They might have studied the addition of halogens to alkenes, so using that as the primary example is good. Also, maybe mention that anti addition can lead to specific stereochemical outcomes, which are important in determining the product's structure.

Let me structure this into paragraphs. First paragraph: Define anti addition, contrast with syn addition, use bromine addition as example. Second paragraph: Mechanism of bromine addition, bromonium ion, backside attack. Third paragraph: Stereochemical outcomes and examples like cis and trans starting materials. Fourth paragraph: Contrast with syn addition in another reaction, like hydrogenation,"""

def test_aggressive_cleaning():
    """Test that the new aggressive cleaning removes ALL thinking content"""
    engine = ArchaeologyEngine(hindsight_service)
    
    print("\n" + "="*80)
    print("AGGRESSIVE THINKING CONTENT REMOVAL TEST")
    print("="*80)
    
    print("\n[TESTING] User's problematic example response...")
    print("\nORIGINAL (PROBLEMATIC) LENGTH:", len(PROBLEMATIC_RESPONSE), "chars")
    print("\nPROBLEMATIC CONTENT SAMPLES:")
    print("  - 'Wait, right, like in the case...'")
    print("  - 'But how exactly does that work?'")
    print("  - 'Hmm, maybe I should stick to the bromine example.'")
    print("  - 'No, wait, HBr with peroxides...'")
    print("  - 'Let me think about the mechanism...'")
    print("  - 'But I'm not sure if that's anti addition.'")
    print("  - 'I need to be careful here.'")
    
    # Clean the response
    cleaned = engine._clean_explanation_text(PROBLEMATIC_RESPONSE)
    
    print("\n[RESULT] CLEANED RESPONSE:")
    print(f"  Length: {len(cleaned)} chars (reduced from {len(PROBLEMATIC_RESPONSE)})")
    print(f"\nCleaned content:\n{cleaned[:500]}...\n")
    
    # Check for remaining thinking patterns
    thinking_patterns = [
        "Wait,", "wait,",
        "But how", "but how",
        "Maybe", "maybe",
        "Hmm,", "hmm,",
        "No, wait", "no, wait",
        "Let me think",
        "But I'm", "but i'm",
        "I'm not sure",
        "Maybe better",
        "I should",
        "Or is it",
        "I need to be careful",
    ]
    
    print("[CHECKING] For remaining thinking patterns:")
    found_issues = []
    for pattern in thinking_patterns:
        if pattern.lower() in cleaned.lower():
            found_issues.append(pattern)
    
    if not found_issues:
        print("  [OK] NO thinking patterns found")
        print("  [OK] Response is CLEAN")
        print("\nVERDICT: AGGRESSIVE CLEANING WORKING!")
        return True
    else:
        print(f"  [ISSUE] Found {len(found_issues)} thinking patterns:")
        for issue in found_issues:
            print(f"    - '{issue}'")
        print("\nVERDICT: Still has thinking content")
        return False

if __name__ == "__main__":
    success = test_aggressive_cleaning()
    exit(0 if success else 1)
