# backend/scripts/seed_demo_data.py
"""
🌱 Pre-populate demo data (works in demo mode).
"""
import asyncio
import os
from datetime import datetime, timedelta
from sys import path as sys_path

sys_path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.hindsight_service import HindsightService
from app.models.memory_types import StudySession, Misconception

async def seed_demo():
    service = HindsightService()
    
    print(f"🧠 Seeding demo data to bank: {service.bank_id}")
    print(f"🔑 API Available: {service.api_available}")
    print("-" * 50)
    
    # Demo sessions (will be stored in memory if API works, or simulated)
    sessions = [
        StudySession(
            topic="recursion", confusion_level=4, error_pattern="base_case_missing",
            hint_used="visual_gift_analogy", outcome="resolved",
            time_spent_seconds=420, emotional_cue="frustrated_then_relieved"
        ),
        StudySession(
            topic="recursion", confusion_level=3, error_pattern="stack_overflow",
            hint_used="draw_call_stack", outcome="partial",
            time_spent_seconds=315, emotional_cue="confused"
        ),
        StudySession(
            topic="dynamic_programming", confusion_level=5, error_pattern="overlapping_subproblems",
            hint_used="memoization_table", outcome="resolved",
            time_spent_seconds=600, emotional_cue="overwhelmed_then_confident"
        ),
    ]
    
    for i, session in enumerate(sessions):
        timestamp = (datetime.now() - timedelta(days=(len(sessions) - i) * 3)).isoformat()
        content = f"Studied {session.topic}: confusion={session.confusion_level}/5"
        
        context = {"type": "StudySession", **session.model_dump(), "timestamp": timestamp}
        result = await service.retain_study_session(content=content, context=context)
        
        status = "✓" if result.get("status") == "success" else "⚠"
        mode = " (demo)" if result.get("demo_mode") else ""
        print(f"{status} Session {i+1}: {session.topic} (confusion={session.confusion_level}){mode}")
    
    print("-" * 50)
    if not service.api_available:
        print(f"⚠️  Running in DEMO MODE - responses are simulated")
        print(f"💡 To enable real Hindsight: Set correct HINDSIGHT_BASE_URL in .env")
    else:
        print(f"✅ Connected to Hindsight API")
    
    print(f"🔗 Demo UI: https://ui.hindsight.vectorize.io/banks/{service.bank_id}")
    print(f"🚀 Backend ready: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(seed_demo())