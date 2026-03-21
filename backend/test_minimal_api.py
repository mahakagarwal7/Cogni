# backend/test_minimal_api.py
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test():
    api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
    base_url = os.getenv("HINDSIGHT_BASE_URL", "").strip().rstrip('/')
    bank_id = os.getenv("HINDSIGHT_USER_BANK_PREFIX") or os.getenv("HINDSIGHT_BANK_ID", "student_demo_001")
    
    print(f"🔍 Testing minimal API call...")
    print(f"   base_url: {repr(base_url)}")
    print(f"   api_key: {api_key[:20] if api_key else None}...")
    
    payload = {
        "bank_id": bank_id,
        "query": "test",
        "strategies": ["semantic"],
        "limit": 1
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try different endpoint paths
    endpoints = ["/recall", "/v1/recall", "/api/recall"]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n🔌 Trying: {repr(url)}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS! Use this endpoint path.")
                    return True
                else:
                    print(f"   ❌ {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test())