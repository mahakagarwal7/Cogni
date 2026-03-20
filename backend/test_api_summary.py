#!/usr/bin/env python3
"""
Integration test for summary feature API endpoints
Tests the actual HTTP endpoints as they would be called from the frontend
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_summary_endpoint():
    """Test POST /memory/summary endpoint"""
    print("="*60)
    print("TEST 1: POST /memory/summary")
    print("="*60)
    
    conversation_text = """
    User: I'm confused about recursion. Why do we need base cases?
    Assistant: Base cases tell the recursion when to stop.
    User: What about dynamic programming?
    Assistant: DP builds on recursion with memoization.
    """
    
    payload = {
        "conversation": conversation_text
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/memory/summary",
                json=payload,
                timeout=30.0
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint responded successfully")
                print(f"\nResponse keys: {data.keys()}")
                
                if 'data' in data:
                    print(f"✅ Data field present")
                    print(f"  - demo_mode: {data['data'].get('demo_mode')}")
                    print(f"  - preview length: {len(data['data'].get('preview', ''))}")
                    print(f"  - summary length: {len(data['data'].get('full_summary', ''))}")
                    
                    return data['data'].get('full_summary', '')
                else:
                    print(f"⚠️  No 'data' field in response")
                    print(f"Response: {data}")
                    
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                
    except httpx.ConnectError:
        print(f"❌ Could not connect to {BASE_URL}")
        print("Make sure the backend is running on port 8000")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
    
    return None

async def test_pdf_endpoint(summary_text):
    """Test POST /memory/summary/pdf endpoint"""
    print("\n" + "="*60)
    print("TEST 2: POST /memory/summary/pdf")
    print("="*60)
    
    if not summary_text:
        print("⏭️  Skipping: No summary provided from previous test")
        return
    
    payload = {
        "summary_text": summary_text
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/memory/summary/pdf",
                json=payload,
                timeout=30.0
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Should be PDF binary data
                if response.headers.get('content-type') == 'application/pdf':
                    print(f"✅ PDF endpoint returned success")
                    print(f"  - Content-Type: {response.headers.get('content-type')}")
                    print(f"  - Content size: {len(response.content)} bytes")
                    
                    # Save to file for inspection
                    with open("test_output.pdf", "wb") as f:
                        f.write(response.content)
                    print(f"✅ Saved PDF to test_output.pdf")
                    
                else:
                    print(f"⚠️  Unexpected content type: {response.headers.get('content-type')}")
                    print(f"Response preview: {response.text[:200]}")
                    
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                
    except httpx.ConnectError:
        print(f"❌ Could not connect to {BASE_URL}")
        print("Make sure the backend is running on port 8000")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all API endpoint tests"""
    print("\n🌐 TESTING SUMMARY API ENDPOINTS\n")
    print("Make sure the backend is running: python run.py\n")
    
    # Test 1: Summary endpoint
    summary = await test_summary_endpoint()
    
    # Test 2: PDF endpoint  
    if summary:
        await test_pdf_endpoint(summary)
    
    print("\n" + "="*60)
    print("✅ API TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
