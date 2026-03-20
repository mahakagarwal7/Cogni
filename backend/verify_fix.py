"""
Verify the original issue is fixed: No planning/thinking in level-based content
"""
import httpx
import asyncio

async def verify_original_issue():
    async with httpx.AsyncClient() as client:
        # Test the exact type of content the user mentioned
        topics_with_levels = [
            ("water cycle", 3, "high_school"),
            ("water cycle", 4, "middle_school"),
            ("drip irrigation", 4, "middle_school"),
        ]
        
        print("=" * 70)
        print("VERIFICATION: Original Issue Resolution")
        print("=" * 70)
        print("\nChecking for planning/meta-instruction content that was problematic:")
        print("- 'Then, I need to break down each stage'")
        print("- 'So no bullet points'")
        print("- 'Four to five paragraphs'")
        print("- 'Use examples like'")
        print("- 'Make sure to mention'")
        print("- 'Avoid technical terms'")
        print("- 'Use active language'")
        print("-" * 70)
        
        problematic_patterns = [
            "then, i need",
            "so no",
            "four to five",
            "use examples like",
            "make sure to mention",
            "avoid technical",
            "use active",
            "then tie",
            "or a journey",
            "so i shouldn",
            "emphasize that",
            "let them visualize",
        ]
        
        for topic, level, audience_name in topics_with_levels:
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": topic, "confusion_level": level},
                timeout=30.0
            )
            
            data = response.json()
            explanation = data.get("data", {}).get("result", {}).get("adaptive_explanation", "")
            
            found = [p for p in problematic_patterns if p in explanation.lower()]
            
            status = "[OK] CLEAN" if not found else f"[ISSUE] {found[0]}"
            print(f"\n{topic.upper()} Level {level} ({audience_name:12}): {status}")
            
            if found:
                # Show the problematic content
                sentences = explanation.split(". ")
                for sent in sentences:
                    if found[0] in sent.lower():
                        print(f"  >> {sent[:100]}...")
            else:
                print(f"  ✓ No planning/meta-instruction content found")
                print(f"  ✓ Pure educational explanation ({len(explanation)} chars)")

asyncio.run(verify_original_issue())
