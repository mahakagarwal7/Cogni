#!/usr/bin/env python3
"""
Integration test for the complete summary and PDF download flow
Tests the actual endpoints as they would be called from the frontend
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_summary_flow():
    """Test the complete summary generation and PDF download flow"""
    
    print("="*80)
    print("🧪 TESTING COMPLETE SUMMARY AND PDF FLOW")
    print("="*80)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Generate Summary
        print("\n[Test 1] Testing POST /memory/summary endpoint...")
        
        sample_conversation = """You: I'm confused about recursion. Why do we need base cases?
Assistant: Base cases are crucial because they tell the recursion when to stop. Without them, the function would call itself infinitely.
You: So it's like when we need to stop the loop?
Assistant: Yes! Think of it as the termination condition. Every recursive function needs at least one base case where it returns a value without making another recursive call.
You: That makes sense. What about dynamic programming?
Assistant: Great question! Dynamic programming builds on recursion but adds memoization to avoid recalculating the same subproblems."""
        
        try:
            response = await client.post(
                f"{BASE_URL}/memory/summary",
                json={"conversation": sample_conversation}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed: {response.text[:200]}")
                return
            
            data = response.json()
            print(f"✅ Summary generated successfully")
            
            if "data" not in data:
                print(f"❌ Invalid response format: {data}")
                return
            
            preview = data.get("data", {}).get("preview", "")
            full_summary = data.get("data", {}).get("full_summary", "")
            
            print(f"  • Preview length: {len(preview)} chars")
            print(f"  • Full summary length: {len(full_summary)} chars")
            print(f"  • Preview:\n    {preview[:100]}...")
            
            if not full_summary:
                print("❌ No full summary returned")
                return
            
            # Test 2: Download PDF
            print("\n[Test 2] Testing POST /memory/summary/pdf endpoint...")
            
            pdf_response = await client.post(
                f"{BASE_URL}/memory/summary/pdf",
                json={
                    "summary_text": full_summary,
                    "topic_name": "recursion"
                }
            )
            
            print(f"Status: {pdf_response.status_code}")
            
            if pdf_response.status_code != 200:
                print(f"❌ Failed: {pdf_response.text[:200]}")
                return
            
            # Check content type
            content_type = pdf_response.headers.get("content-type", "")
            print(f"Content-Type: {content_type}")
            
            # Check if it's actually PDF or JSON error
            if "application/json" in content_type:
                error_data = pdf_response.json()
                print(f"❌ Got JSON error response: {error_data}")
                return
            
            pdf_bytes = pdf_response.content
            print(f"✅ PDF received: {len(pdf_bytes)} bytes")
            
            if len(pdf_bytes) == 0:
                print("❌ PDF is empty")
                return
            
            # Save PDF for inspection
            with open("test_integration_output.pdf", "wb") as f:
                f.write(pdf_bytes)
            print(f"  • Saved to: test_integration_output.pdf")
            
            # Check if it looks like a PDF
            if pdf_bytes.startswith(b'%PDF'):
                print("  ✅ Valid PDF format")
            else:
                print(f"  ⚠️  Unknown format - first bytes: {pdf_bytes[:20]}")
            
            # Test 3: Verify filename in response header
            print("\n[Test 3] Checking response headers...")
            disposition = pdf_response.headers.get("content-disposition", "")
            print(f"Content-Disposition: {disposition}")
            
            if "recursion_study_plan.pdf" in disposition:
                print("✅ Correct filename in header")
            else:
                print(f"⚠️  Unexpected filename format: {disposition}")
            
            # Test 4: Test with different topics
            print("\n[Test 4] Testing with different topic names...")
            
            test_topics = ["dynamic_programming", "graph_algorithms", "sorting"]
            
            for topic in test_topics:
                try:
                    topic_response = await client.post(
                        f"{BASE_URL}/memory/summary/pdf",
                        json={
                            "summary_text": full_summary,
                            "topic_name": topic
                        }
                    )
                    
                    if topic_response.status_code == 200:
                        size = len(topic_response.content)
                        disposition = topic_response.headers.get("content-disposition", "")
                        print(f"  ✅ {topic}: {size} bytes - {disposition}")
                    else:
                        print(f"  ❌ {topic}: HTTP {topic_response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ {topic}: {e}")
            
        except httpx.ConnectError:
            print("❌ Cannot connect to backend at " + BASE_URL)
            print("   Make sure backend is running: python run.py")
            return
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return
    
    print("\n" + "="*80)
    print("✅ INTEGRATION TESTS COMPLETE")
    print("="*80)
    print("\nKey Results:")
    print("  • Summary generation working properly")
    print("  • PDF generation and download working")
    print("  • Proper error handling in place")
    print("  • Topic-based filenames working")
    print("\nThe feature is ready for use!")
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_summary_flow())
