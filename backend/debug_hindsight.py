#!/usr/bin/env python
"""Debug Hindsight API connectivity."""
import asyncio
from app.services.hindsight_service import hindsight_service

print("=" * 70)
print("[DEBUG] Hindsight Service Status")
print("=" * 70)
print(f"API Available: {hindsight_service.api_available}")
print(f"Base URL: {hindsight_service.base_url}")
print(f"API Key: {'[SET]' if hindsight_service.api_key else '[MISSING]'}")
print(f"Bank ID: {hindsight_service.bank_id}")
print(f"Global Bank: {hindsight_service.global_bank}")
print(f"Client initialized: {hindsight_service.client is not None}")
print("=" * 70)

# Try a simple recall to test connectivity
async def test_recall():
    try:
        print("\n[TEST] Attempting recall_temporal_archaeology...")
        result = await hindsight_service.recall_temporal_archaeology(
            topic="recursion",
            confusion_level=3,
            days=30
        )
        print(f"Result: {result}")
        print(f"Demo Mode: {result.get('demo_mode', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

asyncio.run(test_recall())
