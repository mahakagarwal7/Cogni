
"""
👤 Feature 3: Cognitive Shadow
Your digital twin predicts where you'll struggle next.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from typing import Dict, Any

class ShadowEngine:
    """
    Cognitive Shadow Engine - Predictive insights from patterns.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
        self.llm = llm_service
    
    async def get_prediction(self, current_topic: str = None, days: int = 7) -> Dict[str, Any]:
        """
        Get predictive insights based on current topic being studied OR conversation history.
        If current_topic is provided, predicts what comes after that topic.
        Otherwise queries Hindsight for study history.
        """
        # Priority 1: Use current topic if provided (most immediate and relevant)
        if current_topic:
            next_challenge = self.hindsight._predict_next_challenge([current_topic], [])
            return {
                "feature": "cognitive_shadow",
                "prediction": next_challenge["prediction"],
                "confidence": min(next_challenge["confidence"] + 0.1, 0.95),  # Boost confidence for current topic
                "evidence": next_challenge["evidence"],
                "current_topic": current_topic,
                "recent_topics": [current_topic],
                "demo_mode": False
            }
        
        # Priority 2: Query Hindsight for conversation history
        prediction = await self.hindsight.reflect_cognitive_shadow(days=days)
        
        # Optionally use LLM to enhance the prediction text
        prediction_text = prediction.get("prediction", "Keep practicing consistently")
        
        if self.llm.available and prediction.get("recent_topics"):
            # LLM enhances prediction only if we have real history
            topics_str = ", ".join(prediction.get("recent_topics", [])[:3])
            prompt = f"""Refine this prediction into a more engaging, actionable statement:

Studied: {topics_str}
Current prediction: {prediction_text}

Make it more specific and encouraging (under 30 words). Respond with ONLY the refined prediction."""
            try:
                refined = self.llm.generate(prompt, max_tokens=50, temperature=0.4)
                if refined and not any(c in refined for c in ['<', '{', '[']):
                    prediction_text = refined.strip()
            except Exception as e:
                print(f"[DEBUG] LLM refinement skipped: {e}")
                # Keep original prediction
        
        return {
            "feature": "cognitive_shadow",
            "prediction": prediction_text,
            "confidence": prediction.get("confidence", 0.78),
            "evidence": prediction.get("evidence", []),
            "recent_topics": prediction.get("recent_topics", []),
            "demo_mode": prediction.get("demo_mode", True)
        }
    
    async def get_learning_patterns(self) -> Dict[str, Any]:
        """
        Summarize user's learning patterns using Groq LLM.
        """
        # Demo patterns - in real app would analyze actual data
        patterns_list = [
            "Visual learner (85% success with diagrams)",
            "Struggles under time pressure",
            "Prefers step-by-step explanations",
            "Better at algorithmic concepts than mathematical proofs"
        ]
        
        # Use LLM to generate pattern analysis summary
        prompt = f"""Summarize these learning patterns into 1 actionable insight:
- {chr(10).join(patterns_list)}

Keep to 1 sentence, starting with 'You'."""
        
        summary = self.llm.generate(prompt, max_tokens=80)
        
        return {
            "feature": "learning_patterns",
            "summary": summary.strip(),
            "patterns": [
                {
                    "pattern": "Visual learner",
                    "evidence": "85% success rate with diagram-based hints",
                    "confidence": 0.89
                },
                {
                    "pattern": "Struggles under time pressure",
                    "evidence": "Confusion levels 2x higher in timed sessions",
                    "confidence": 0.76
                },
                {
                    "pattern": "Prefers step-by-step explanations",
                    "evidence": "Resolved 90% of problems with structured hints",
                    "confidence": 0.82
                }
            ],
            "demo_mode": not self.llm.available
        }