#!/usr/bin/env python3
"""
Test script for summary feature endpoints
Tests:
1. Conversation summary generation
2. PDF generation from summary
"""

import sys
import asyncio
import json
from app.services.summary_service import summary_service

async def test_summary_generation():
    """Test the summary generation endpoint"""
    print("="*60)
    print("TEST 1: Conversation Summary Generation")
    print("="*60)
    
    # Sample conversation
    conversation = """
    User: I'm confused about recursion. Why do we need base cases?
    Assistant: Base cases are crucial because they tell the recursion when to stop. Without them, the function would call itself infinitely.
    User: So it's like when we need to stop the loop?
    Assistant: Yes! Think of it as the termination condition. Every recursive function needs at least one base case where it returns a value without making another recursive call.
    User: That makes sense. What about dynamic programming? Is it related to recursion?
    Assistant: Great question! Dynamic programming builds on recursion but adds memoization to avoid recalculating the same subproblems.
    User: Oh, I see. So memoization is just caching results?
    Assistant: Exactly! You store results of expensive function calls and return the cached result when the same inputs occur again.
    """
    
    try:
        result = await summary_service.generate_summary(conversation)
        
        print(f"✅ Summary generation succeeded!")
        print(f"\nPreview (first 200 chars):")
        print(result['preview'][:200] + "..." if len(result['preview']) > 200 else result['preview'])
        print(f"\nFull Summary (first 300 chars):")
        print(result['full_summary'][:300] + "..." if len(result['full_summary']) > 300 else result['full_summary'])
        print(f"\nDemo Mode: {result['demo_mode']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_pdf_generation(summary_text):
    """Test the PDF generation"""
    print("\n" + "="*60)
    print("TEST 2: PDF Generation")
    print("="*60)
    
    if not summary_text:
        print("❌ Skipping PDF test: No summary provided")
        return
    
    try:
        pdf_bytes = summary_service.generate_pdf(summary_text, "Test Learning Summary")
        
        if pdf_bytes:
            print(f"✅ PDF generation succeeded!")
            print(f"PDF size: {len(pdf_bytes)} bytes")
            
            # Save to file for manual inspection
            with open("test_summary.pdf", "wb") as f:
                f.write(pdf_bytes)
            print("✅ Saved to test_summary.pdf")
            
        else:
            print("❌ PDF generation returned empty")
            
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("\n🧪 TESTING SUMMARY FEATURE\n")
    
    # Test 1: Summary generation
    summary_result = await test_summary_generation()
    
    # Test 2: PDF generation
    if summary_result:
        await test_pdf_generation(summary_result.get('full_summary', ''))
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
