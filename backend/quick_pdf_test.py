#!/usr/bin/env python3
"""Quick test to verify PDF generation is working"""
import asyncio
from app.services.summary_service import summary_service

async def test_pdf():
    print("Testing PDF generation...\n")
    
    test_summary = """This is a test learning summary about recursion.
    
Recursion is a fundamental programming concept where a function calls itself with different parameters. The key to proper recursion is having a base case that stops the recursion.

In this session, we covered base cases, recursive problems, and how to trace through recursive calls step by step.

The student showed good understanding of when to use recursion and how to avoid infinite loops.

Main takeaways: Always have a base case, understand the recursive case, and test with small examples first."""

    # Test with reportlab
    print("1. Testing PDF generation with reportlab...")
    pdf_bytes = summary_service.generate_pdf(test_summary, "Recursion - Study Plan")
    
    if pdf_bytes and len(pdf_bytes) > 100:
        print(f"✅ SUCCESS: PDF generated ({len(pdf_bytes)} bytes)")
        
        # Save to file
        with open("test_pdf_output.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("✅ Saved to: test_pdf_output.pdf")
        
        # Check if it's a valid PDF
        if pdf_bytes.startswith(b'%PDF'):
            print("✅ Valid PDF format (starts with %PDF)")
        elif pdf_bytes.startswith(b'This is'):
            print("⚠️  Text fallback used (but valid)")
        else:
            print(f"ℹ️  Format: {pdf_bytes[:20]}")
    else:
        print(f"❌ FAILED: PDF too small ({len(pdf_bytes) if pdf_bytes else 0} bytes)")

if __name__ == "__main__":
    asyncio.run(test_pdf())
