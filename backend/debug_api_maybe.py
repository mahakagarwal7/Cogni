"""
Debug: Check the actual maybe contexts from API
"""
import httpx
import asyncio

async def debug_maybe():
    async with httpx.AsyncClient() as client:
        for level in [2, 4]:
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
                    
                    # Analyze context
                    is_hedging = any(hm in sent.lower() for hm in [
                        "maybe you", "maybe i", "maybe it", "maybe that",
                        "maybe this", "maybe they", "maybe could", "maybe the"
                    ])
                    print(f"  ^ This seems {'[QUESTIONABLE - hedging]' if is_hedging else '[OK - legitimate maybe]'}")

asyncio.run(debug_maybe())
