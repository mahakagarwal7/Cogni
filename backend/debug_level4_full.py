"""
Debug level 4 for let me and maybe contexts
"""
import httpx
import asyncio

async def debug():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/study/archaeology",
            params={"topic": "Anti-addition reactions", "confusion_level": 4},
            timeout=30.0
        )
        
        result_data = response.json().get("data", {}).get("result", {})
        explanation = result_data.get("adaptive_explanation", "")
        
        print("Full Level 4 Explanation:")
        print("=" * 70)
        print(explanation)
        print("\n" + "=" * 70)
        
        # Find and show sentences with "maybe" or "let me"
        print("\nProblematic sentences:")
        sentences = explanation.split(". ")
        for i, sent in enumerate(sentences):
            if "maybe" in sent.lower() or "let me" in sent.lower():
                print(f"\nSentence {i+1}:")
                print(f"  {sent}")

asyncio.run(debug())
