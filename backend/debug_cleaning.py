import sys
sys.path.insert(0, 'app')

from engines.archaeology_engine import ArchaeologyEngine

# Setup
engine = ArchaeologyEngine()

problematic = """Wait, right, like in the case of reactions. So anti addition is basically the opposite. But how exactly does that work? Hmm, maybe I should stick to the bromine example. No, wait, HBr with peroxides does Markovnikov's, but HBr without peroxides does anti-Markovnikov's. Let me think about the mechanism. But I'm not sure if that's anti addition. I need to be careful here.

Anti addition is a type of reaction in organic chemistry where two substituents add to opposite sides of a double bond. It's the opposite of syn addition, where both groups add to the same side. When bromine adds to an alkene, it forms a bromonium ion intermediate. The bromide ion then attacks from the opposite side, leading to anti addition. That's a key point. So the spatial arrangement is important here. The molecule can't rotate once the double bond is...

Maybe I could use another example like HCl? Or maybe bromine in water? No, wait, I think I should stick to the core concept first. Actually, let me think about stereochemistry. But I'm not entirely confident about this explanation. I think examples would help make it clearer. Let me be more direct about the mechanism.

Anti addition follows a specific mechanism: 1. The alkene approaches the electrophile (like Br₂), which becomes polarized. 2. A pi bond forms with the front lobe of the double bond, creating a bromonium ion. 3. Due to the ring strain and geometry, the nucleophile can only attack from the back. 4. This results in opposite stereochemistry."""

cleaned = engine._clean_explanation_text(problematic)

print("=" * 70)
print("CLEANED OUTPUT:")
print("=" * 70)
print(cleaned)
print("=" * 70)

# Check for maybe/Maybe
if "maybe" in cleaned.lower():
    print("\nFOUND 'maybe' in cleaned text!")
    # Find the context
    lines = cleaned.split(". ")
    for i, line in enumerate(lines):
        if "maybe" in line.lower():
            print(f"  Sentence {i+1}: {line}")
else:
    print("\nNO 'maybe' found in cleaned text - GOOD!")

# Show metrics
print(f"\nOriginal length: {len(problematic)}")
print(f"Cleaned length: {len(cleaned)}")
print(f"Reduction: {(1 - len(cleaned)/len(problematic))*100:.1f}%")
