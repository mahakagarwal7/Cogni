"""
Debug levels 1 and 4 for their maybe contexts
"""
import httpx
import asyncio

async def debug_maybe():
    async with httpx.AsyncClient() as client:
        for level in [1, 4]:
            response = await client.get(
                "http://localhost:8000/api/study/archaeology",
                params={"topic": "Anti-addition reactions", "confusion_level": level},
                timeout=30.0
            )
            
            result_data = response.json().get("data", {}).get("result", {})
            explanation = result_data.get("adaptive_explanation", "")
            
            print(f"\n{'='*70}")
            print(f"CONFUSION LEVEL {level}")
            print('='*70)
            
            # Find and show sentences with "maybe"
            sentences = explanation.split(". ")
            for i, sent in enumerate(sentences):
                if "maybe" in sent.lower():
                    print(f"\nSentence {i+1}:")
                    print(f"  {sent}")

asyncio.run(debug_maybe())
