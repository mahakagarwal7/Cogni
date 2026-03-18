# backend/app/engines/archaeology_engine.py
from app.services.hindsight_service import HindsightService, hindsight_service
from app.models.memory_types import StudySession
from typing import Dict, Any

class ArchaeologyEngine:
    """
    🔍 Feature 1: Temporal Cognitive Archaeology
    Logic: How to find and interpret past confusion patterns
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
    
    async def find_past_struggles(self, topic: str, confusion_level: int, days: int = 30) -> Dict[str, Any]:
        """
        Main method: Find similar confusion moments + what helped.
        """
        # Call core service (doesn't talk to Hindsight directly!)
        result = await self.hindsight.recall_temporal_archaeology(
            topic=topic,
            confusion_level=confusion_level,
            days=days
        )
        
        # Add feature-specific analysis
        return {
            "feature": "temporal_archaeology",
            "query": {"topic": topic, "confusion_level": confusion_level},
            "result": result,
            "actionable": len(result.get("what_helped_before", [])) > 0
        }
    
    async def log_study_session(self, session: StudySession) -> Dict[str, Any]:
        """
        Save a new study session to memory.
        """
        content = f"Studied {session.topic}: confusion={session.confusion_level}/5, error={session.error_pattern}"
        
        result = await self.hindsight.retain_study_session(
            content=content,
            context=session.model_dump()
        )
        
        return {
            "feature": "study_log",
            "status": result.get("status"),
            "session": session.model_dump()
        }