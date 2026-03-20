import sys
sys.path.insert(0, 'app')

from engines.archaeology_engine import ArchaeologyEngine

# The long response from the test
LONGER_RESPONSE = """"anti addition" for JEE/NEET aspirants. Let me start by recalling what I know. Anti addition is a type of reaction in organic chemistry where two substituents add to opposite sides of a double bond. Wait, right, like in the case of bromine adding to an alkene. But how exactly does that work?

First, I should define anti addition clearly. It's the opposite of syn addition, where both groups add to the same side. Maybe I can compare them using examples. Like, bromine water with an alkene gives anti addition, while maybe HBr with peroxides gives syn? No, wait, HBr with peroxides is anti-Markovnikov but still anti addition? Hmm, maybe I should stick to the bromine example.

Let me think about the mechanism. When bromine adds to an alkene, it forms a bromonium ion intermediate. The bromide ion then attacks from the opposite side, leading to anti addition. That's a key point. So the spatial arrangement is important here. The molecule can't rotate once the double bond is broken, so the attack has to happen from the opposite face.

Wait, another example could be the addition of hydrogen halides in the presence of peroxides. But I'm not sure if that's anti addition. Maybe better to focus on the bromine example. Also, maybe mention that anti addition is common in halogen addition reactions. Oh, and the diastereomers formed can be a result of this. For instance, if the alkene is cis or trans, the product's stereochemistry will differ.

I should also mention the anti addition in the context of hydroboration-oxidation, but wait, hydroboration is syn addition. So maybe avoid that. Stick to bromine addition. Also, maybe contrast with syn addition in another reaction. For example, in hydration using H2O and H2SO4, the addition is anti-Markovnikov but syn? No, wait, acid-catalyzed hydration is Markovnikov and syn? Or is it anti? I need to be careful here. Maybe it's better to use the bromine addition as the main example and compare with another reaction where syn addition occurs, like hydrogenation with H2 and a catalyst.

Another point to consider is the use of the term "anti" in the context of stereochemistry. It refers to the direction from which the reagents approach the molecule. So, when you have a planar molecule like an alkene, adding two groups from opposite sides gives anti addition. This is different from syn addition where both groups add to the same face.

I need to make sure the explanation is clear and uses examples that are familiar to JEE/NEET students. They might have studied the addition of halogens to alkenes, so using that as the primary example is good. Also, maybe mention that anti addition can lead to specific stereochemical outcomes, which are important in determining the product's structure.

Let me structure this into paragraphs. First paragraph: Define anti addition, contrast with syn addition, use bromine addition as example. Second paragraph: Mechanism of bromine addition, bromonium ion, backside attack. Third paragraph: Stereochemical outcomes and examples like cis and trans starting materials. Fourth paragraph: Contrast with syn addition in another reaction, like hydrogenation,"""

engine = ArchaeologyEngine()

# Split and analyze sentence by sentence
sentences = LONGER_RESPONSE.replace("! ", "! ").replace("? ", "? ").split(". ")
print(f"Total sentences: {len(sentences)}\n")

print("SENTENCES WITH 'MAYBE':")
for i, s in enumerate(sentences):
    if "maybe" in s.lower():
        would_filter = engine._is_thinking_sentence(s + ".")
        status = "[FILTERED]" if would_filter else "[KEPT!!!]"
        print(f"  {i:2d} {status} : {s[:80]}...")

print("\n" + "=" * 70)
cleaned = engine._clean_explanation_text(LONGER_RESPONSE)
print(f"Original: {len(LONGER_RESPONSE)} chars")
print(f"Cleaned: {len(cleaned)} chars")

if "maybe" in cleaned.lower():
    print("\n[ISSUE] Found 'maybe' in cleaned text - checking context:")
    lines = cleaned.split(". ")
    for line in lines:
        if "maybe" in line.lower():
            print(f"  >> {line[:100]}...")
else:
    print("\n[OK] NO 'maybe' in cleaned text!")
