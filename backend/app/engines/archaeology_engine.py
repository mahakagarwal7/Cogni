# backend/app/engines/archaeology_engine.py
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from app.models.memory_types import StudySession
from typing import Dict, Any

class ArchaeologyEngine:
    """
    🔍 Feature 1: Temporal Cognitive Archaeology
    Logic: How to find and interpret past confusion patterns
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
        self.llm = llm_service
    
    def _calculate_confidence_from_confusion(self, confusion_level: int) -> float:
        """
        Convert confusion_level (1-5) to system confidence (0.5-0.95).
        Higher confusion = lower confidence (situation is less clear).
        """
        if confusion_level <= 1:
            return 0.95
        elif confusion_level == 2:
            return 0.85
        elif confusion_level == 3:
            return 0.75
        elif confusion_level == 4:
            return 0.60
        else:  # 5
            return 0.50
    
    async def find_past_struggles(self, topic: str, confusion_level: int, days: int = 30) -> Dict[str, Any]:
        """
        Main method: Find similar confusion moments + what helped, with LLM-generated recommendation.
        """
        # Call core service to find historical struggles
        result = await self.hindsight.recall_temporal_archaeology(
            topic=topic,
            confusion_level=confusion_level,
            days=days
        )
        
        # Use LLM to enhance recommendation only if we have helpful hints to base it on
        what_helped = result.get("what_helped_before", [])
        if what_helped and any(h.get("hint_used") for h in what_helped):
            hints_summary = "\n".join([f"- {h.get('hint_used', 'unknown')}" for h in what_helped[:3] if h.get("hint_used")])
            if hints_summary:
                prompt = f"""Based on what helped before for {topic}:

{hints_summary}

Provide ONE specific actionable step. Respond with ONLY the step in 1 sentence."""
                
                recommendation_raw = self.llm.generate(prompt, max_tokens=60, temperature=0.3)
                # Aggressively clean up LLM response
                recommendation = recommendation_raw.strip()
                if "<think>" in recommendation:
                    recommendation = recommendation.split("</think>", 1)[-1].strip()
                # Remove any remaining markdown or formatting
                recommendation = recommendation.lstrip("\n*#- ").strip()
                # Keep only first sentence
                if "." in recommendation:
                    recommendation = recommendation.split(".")[0] + "."
                if recommendation and len(recommendation) > 10:  # Only use if meaningful
                    result["recommendation"] = recommendation
        
        # Add feature-specific analysis with single confidence based on confusion_level
        return {
            "feature": "temporal_archaeology",
            "query": {"topic": topic, "confusion_level": confusion_level},
            "confidence": self._calculate_confidence_from_confusion(confusion_level),
            "result": result,
            "actionable": len(what_helped) > 0
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