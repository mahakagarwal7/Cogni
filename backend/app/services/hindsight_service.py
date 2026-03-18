# backend/app/services/hindsight_service.py
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class HindsightService:
    """
    🧠 THE CORE: Unified memory service.
    Defaults to demo mode if API is unavailable.
    """
    
    def __init__(self):
        self.api_key = os.getenv("HINDSIGHT_API_KEY")
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").rstrip('/')
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "student_demo_001")
        self.global_bank = os.getenv("HINDSIGHT_GLOBAL_BANK", "global_wisdom_public")
        
        # Flag: Is real API available?
        self.api_available = bool(self.api_key and self.base_url)
    
    # ==================== RETAIN OPERATIONS ====================
    
    async def retain_study_session(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a study session to memory."""
        if not self.api_available:
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
        
        # TODO: Replace with correct Hindsight API call once endpoint is confirmed
        # For now, simulate success
        return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
    
    async def retain_misconception(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a misconception for Socratic Ghost."""
        if not self.api_available:
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
        
        # TODO: Replace with correct Hindsight API call
        return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
    
    # ==================== RECALL OPERATIONS ====================
    
    async def recall_temporal_archaeology(self, topic: str, confusion_level: int, days: int = 30) -> Dict:
        """Feature 1: Find similar confusion moments in the past."""
        if not self.api_available:
            return self._get_demo_archaeology_response(topic, confusion_level)
        
        # TODO: Replace with actual Hindsight API call
        return self._get_demo_archaeology_response(topic, confusion_level)
    
    async def recall_socratic_history(self, concept: str) -> Dict:
        """Feature 2: Find past misconceptions about a concept."""
        if not self.api_available:
            return self._get_demo_socratic_response(concept)
        
        # TODO: Replace with actual Hindsight API call
        return self._get_demo_socratic_response(concept)
    
    async def recall_all_memories(self, limit: int = 10) -> List[Dict]:
        """Memory Inspector: Get all memories for transparency."""
        if not self.api_available:
            return self._get_demo_memories(limit)
        
        # TODO: Replace with actual Hindsight API call
        return self._get_demo_memories(limit)
    
    # ==================== REFLECT OPERATIONS ====================
    
    async def reflect_cognitive_shadow(self, days: int = 7) -> Dict:
        """Feature 3: Synthesize patterns into predictive insights."""
        if not self.api_available:
            return self._get_demo_shadow_response()
        
        # TODO: Replace with actual Hindsight API call
        return self._get_demo_shadow_response()
    
    async def recall_global_contagion(self, error_pattern: str) -> Dict:
        """Feature 5: Query global wisdom bank for peer patterns."""
        if not self.api_available:
            return self._get_demo_contagion_response(error_pattern)
        
        # TODO: Replace with actual Hindsight API call
        return self._get_demo_contagion_response(error_pattern)
    
    # ==================== DEMO RESPONSES (Fallback) ====================
    
    def _get_demo_archaeology_response(self, topic: str, confusion_level: int) -> Dict:
        """Realistic demo response for Temporal Archaeology."""
        return {
            "similar_moments": 3,
            "what_helped_before": [
                {
                    "timestamp": "2026-03-10T14:30:00Z",
                    "hint_used": "visual_gift_analogy",
                    "outcome": "resolved",
                    "confidence": 0.92
                },
                {
                    "timestamp": "2026-03-15T09:15:00Z", 
                    "hint_used": "draw_call_stack",
                    "outcome": "resolved",
                    "confidence": 0.87
                }
            ],
            "recommendation": f"Last time you felt this confused about {topic}, 'visual_gift_analogy' helped. Try that approach again.",
            "demo_mode": True
        }
    
    def _get_demo_socratic_response(self, concept: str) -> Dict:
        """Realistic demo response for Socratic Ghost."""
        return {
            "total_found": 2,
            "resolved_count": 1,
            "unresolved_count": 1,
            "history": [
                {
                    "content": f"Misconception: {concept} - 'incorrect belief'",
                    "context": {
                        "type": "Misconception",
                        "concept": concept,
                        "resolved": True,
                        "question_asked": "What happens if we test the edge case?"
                    },
                    "timestamp": "2026-03-12T10:00:00Z",
                    "confidence": 0.89
                }
            ],
            "next_question": f"Last time you had this misconception about {concept}, asking about edge cases helped. What do you think happens in the simplest possible case?",
            "demo_mode": True
        }
    
    def _get_demo_memories(self, limit: int) -> List[Dict]:
        """Realistic demo memories for Memory Inspector."""
        return [
            {
                "id": f"mem_{i}",
                "content": f"Studied recursion: confusion={4-i%3}/5",
                "context": {
                    "type": "StudySession",
                    "topic": "recursion",
                    "confusion_level": 4-i%3,
                    "outcome": "resolved" if i%2==0 else "partial"
                },
                "timestamp": (datetime.now() - timedelta(days=i*2)).isoformat(),
                "confidence": 0.85 + (i*0.03),
                "tags": ["recursion", "study_session"]
            }
            for i in range(min(limit, 5))
        ]
    
    def _get_demo_shadow_response(self) -> Dict:
        """Realistic demo response for Cognitive Shadow."""
        return {
            "prediction": "Your Cognitive Twin predicts you'll struggle with tree traversal recursion tomorrow. Prep with the 'unwrapping gifts' visual exercise first.",
            "confidence": 0.84,
            "evidence": [
                "You learn recursion 40% faster with visual analogies",
                "Base case errors increase when tired (after 8pm)"
            ],
            "demo_mode": True
        }
    
    def _get_demo_contagion_response(self, error_pattern: str) -> Dict:
        """Realistic demo response for Metacognitive Contagion."""
        return {
            "community_size": 47,
            "top_strategy": "visual_analogy",
            "success_rate": 0.82,
            "privacy_note": "Aggregated from anonymized peer data",
            "demo_mode": True
        }
    
    # ==================== HELPERS ====================
    
    def _generate_recommendation(self, helpful_patterns: List[Dict]) -> str:
        """Generate personalized recommendation from past patterns."""
        if not helpful_patterns:
            return "Try breaking the problem into smaller steps and explaining each aloud."
        
        hints = [p["hint_used"] for p in helpful_patterns if p.get("hint_used")]
        if hints:
            most_helpful = max(set(hints), key=hints.count)
            return f"Last time you felt this confused, '{most_helpful}' helped. Try that approach again."
        
        return "Review the foundational concept first, then attempt the problem again."


# Singleton instance for easy import
hindsight_service = HindsightService()