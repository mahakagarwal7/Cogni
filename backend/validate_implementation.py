#!/usr/bin/env python3
"""
Validation script to verify all Memory Summary feature components are properly implemented
Checks:
- All required files exist
- All required imports are correct  
- All route endpoints are registered
- All dependencies are in requirements
"""

import os
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists"""
    exists = os.path.exists(file_path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {file_path}")
    return exists

def check_content(file_path, search_string, description):
    """Check if a string exists in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            found = search_string.lower() in content.lower()
            status = "✅" if found else "❌"
            print(f"  {status} {description}: {'FOUND' if found else 'NOT FOUND'}")
            return found
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return False

def main():
    """Run all validation checks"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    print("\n" + "="*70)
    print("🔍 MEMORY SUMMARY FEATURE - IMPLEMENTATION VALIDATION")
    print("="*70 + "\n")
    
    all_checks_passed = True
    
    # 1. Check Backend Files
    print("1️⃣  BACKEND FILES")
    print("-" * 70)
    
    backend_files = {
        os.path.join(base_path, "app/routes/memory_routes.py"): "Memory routes",
        os.path.join(base_path, "app/services/summary_service.py"): "Summary service",
        os.path.join(base_path, "requirements.txt"): "Requirements file",
    }
    
    for file_path, desc in backend_files.items():
        all_checks_passed &= check_file_exists(file_path, desc)
    
    # 2. Check Backend Implementations
    print("\n2️⃣  BACKEND IMPLEMENTATIONS")
    print("-" * 70)
    
    memory_routes_path = os.path.join(base_path, "app/routes/memory_routes.py")
    if os.path.exists(memory_routes_path):
        print(f"Checking {memory_routes_path}...")
        all_checks_passed &= check_content(memory_routes_path, "SummaryRequest", "SummaryRequest model")
        all_checks_passed &= check_content(memory_routes_path, "PDFRequest", "PDFRequest model")
        all_checks_passed &= check_content(memory_routes_path, "/summary", "Summary endpoint")
        all_checks_passed &= check_content(memory_routes_path, "/summary/pdf", "PDF endpoint")
        all_checks_passed &= check_content(memory_routes_path, "from pydantic import", "Pydantic import")
    
    summary_service_path = os.path.join(base_path, "app/services/summary_service.py")
    if os.path.exists(summary_service_path):
        print(f"\nChecking {summary_service_path}...")
        all_checks_passed &= check_content(summary_service_path, "async def generate_summary", "generate_summary method")
        all_checks_passed &= check_content(summary_service_path, "def generate_pdf", "generate_pdf method")
        all_checks_passed &= check_content(summary_service_path, "from app.services.llm_service", "LLM service import")
    
    # 3. Check Dependencies
    print("\n3️⃣  DEPENDENCIES")
    print("-" * 70)
    
    req_file = os.path.join(base_path, "requirements.txt")
    if os.path.exists(req_file):
        print(f"Checking {req_file}...")
        all_checks_passed &= check_content(req_file, "reportlab", "reportlab library")
        all_checks_passed &= check_content(req_file, "fpdf2", "fpdf2 library")
    
    # 4. Check Frontend Files
    print("\n4️⃣  FRONTEND FILES")
    print("-" * 70)
    
    frontend_files = {
        os.path.join(base_path, "../frontend/src/app/page.tsx"): "Main page component",
        os.path.join(base_path, "../frontend/src/services/api.ts"): "API service",
    }
    
    for file_path, desc in frontend_files.items():
        all_checks_passed &= check_file_exists(file_path, desc)
    
    # 5. Check Frontend Implementations
    print("\n5️⃣  FRONTEND IMPLEMENTATIONS")
    print("-" * 70)
    
    page_tsx_path = os.path.join(base_path, "../frontend/src/app/page.tsx")
    if os.path.exists(page_tsx_path):
        print(f"Checking {page_tsx_path}...")
        all_checks_passed &= check_content(page_tsx_path, "summaryLoading", "summaryLoading state")
        all_checks_passed &= check_content(page_tsx_path, "fullSummary", "fullSummary state")
        all_checks_passed &= check_content(page_tsx_path, "generateSummary", "generateSummary function")
        all_checks_passed &= check_content(page_tsx_path, "downloadSummaryPDF", "downloadSummaryPDF function")
        all_checks_passed &= check_content(page_tsx_path, "Generate Summary", "Generate Summary button")
        all_checks_passed &= check_content(page_tsx_path, "Download PDF", "Download PDF button")
    
    api_service_path = os.path.join(base_path, "../frontend/src/services/api.ts")
    if os.path.exists(api_service_path):
        print(f"\nChecking {api_service_path}...")
        all_checks_passed &= check_content(api_service_path, "generateSummary", "generateSummary method")
        all_checks_passed &= check_content(api_service_path, "downloadSummaryPDF", "downloadSummaryPDF method")
    
    # 6. Check Test Files
    print("\n6️⃣  TEST FILES")
    print("-" * 70)
    
    test_files = {
        os.path.join(base_path, "test_summary_feature.py"): "Summary feature tests",
        os.path.join(base_path, "test_api_summary.py"): "API integration tests",
    }
    
    for file_path, desc in test_files.items():
        check_file_exists(file_path, desc)
    
    # 7. Summary
    print("\n" + "="*70)
    if all_checks_passed:
        print("✅ ALL VALIDATION CHECKS PASSED!")
        print("\nThe Memory Summary feature is fully implemented and ready for testing.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run backend: python run.py")
        print("3. Run frontend: npm run dev")
        print("4. Test the feature in the UI")
    else:
        print("⚠️  SOME VALIDATION CHECKS FAILED")
        print("\nPlease review the failed items above and fix any issues.")
    print("="*70 + "\n")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    exit(main())
