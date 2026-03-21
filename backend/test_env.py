
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Environment Variables Check:")
print("=" * 50)

api_key = os.getenv("HINDSIGHT_API_KEY")
base_url = os.getenv("HINDSIGHT_BASE_URL")
bank_prefix = os.getenv("HINDSIGHT_USER_BANK_PREFIX") or os.getenv("HINDSIGHT_BANK_ID") or "student_demo_001"

print(f"✅ API Key: {'Set' if api_key else '❌ NOT SET'}")
if api_key:
    print(f"   Value: {api_key[:20]}... (first 20 chars)")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Has spaces: {'Yes' if ' ' in api_key else 'No'}")

print(f"\n✅ Base URL: {base_url or '❌ NOT SET'}")
print(f"✅ User Bank Prefix: {bank_prefix or '❌ NOT SET'}")

api_available = bool(api_key and base_url)
print(f"\n🎯 API Available: {api_available}")

if not api_available:
    print("\n❌ FIX NEEDED:")
    if not api_key:
        print("   - HINDSIGHT_API_KEY is missing or empty")
    if not base_url:
        print("   - HINDSIGHT_BASE_URL is missing or empty")
else:
    print("\n✅ Environment looks good!")