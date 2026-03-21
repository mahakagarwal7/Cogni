
"""
👤 Feature 3: Cognitive Shadow
Your digital twin predicts where you'll struggle next.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from typing import Dict, Any, List

class ShadowEngine:
    """
    Cognitive Shadow Engine - Predictive insights from patterns.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
        self.llm = llm_service

    def _format_insights(self, insights: List[Dict[str, Any]]) -> str:
        """Convert user insights into compact prompt context."""
        if not insights:
            return "No prior insight history available."

        lines: List[str] = []
        for row in insights[:5]:
            data = row.get("data") if isinstance(row.get("data"), dict) else {}
            topic = data.get("topic", "general")
            issue = data.get("issue", "unclear_concept")
            style = data.get("preferred_style", "guided")
            lines.append(f"- topic={topic}; issue={issue}; preferred_style={style}")

        return "\n".join(lines)
    
    async def _retain_interaction(self, content: str, user_id: str, topic: str, engine_feature: str, interaction_data: Dict[str, Any]) -> None:
        """
        CRITICAL HELPER: Retain interaction to hindsight memory.
        Called after EVERY engine interaction to build persistent memory.
        No errors here should block the main response flow (wrapped in try/except).
        """
        try:
            metadata = {
                "user_id": user_id,
                "topic": topic,
                "engine_feature": engine_feature,
                "interaction_type": "tutoring_session",
                "timestamp": str(__import__("datetime").datetime.now().isoformat()),
                **{f"data_{k}": str(v) for k, v in interaction_data.items()}
            }
            
            # Asynchronously retain without blocking
            await self.hindsight.retain_study_session(
                content=content,
                context=metadata
            )
            print(f"✓ [RETAINED] {engine_feature} interaction for user={user_id}, topic={topic}")
        except Exception as e:
            # Never block the main flow - just log warnings
            print(f"⚠ [WARNING] Failed to retain interaction: {str(e)}")
    
    async def get_prediction(self, current_topic: str = None, days: int = 7, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Get predictive insights based on current topic being studied OR conversation history.
        If current_topic is provided, predicts what comes after that topic.
        Otherwise queries Hindsight for study history.
        
        CRITICAL: Automatically retains this interaction to hindsight for future recalls.
        """
        # Priority 1: Use current topic if provided (most immediate and relevant)
        if current_topic:
            from uuid import uuid4
            response_id = str(uuid4())
            synthesis = await self.hindsight.reflect_cognitive_shadow(
                days=days,
                user_id=user_id,
                current_topic=current_topic,
            )
            next_challenge = self.hindsight._predict_next_challenge([current_topic], [])
            result = {
                "response_id": response_id,
                "feature": "cognitive_shadow",
                "prediction": synthesis.get("prediction", next_challenge["prediction"]),
                "confidence": min(next_challenge["confidence"] + 0.1, 0.95),  # Boost confidence for current topic
                "evidence": synthesis.get("evidence", next_challenge["evidence"]),
                "current_topic": current_topic,
                "recent_topics": synthesis.get("recent_topics", [current_topic]),
                "demo_mode": synthesis.get("demo_mode", False)
            }
            
            # ⚡ CRITICAL: Retain this interaction
            await self._retain_interaction(
                content=f"Shadow prediction query for {current_topic}",
                user_id=user_id,
                topic=current_topic,
                engine_feature="shadow",
                interaction_data={
                    "prediction": result["prediction"],
                    "confidence": result["confidence"]
                }
            )
            
            return result
        
        # Priority 2: Query Hindsight for conversation history
        from uuid import uuid4
        response_id = str(uuid4())
        prediction = await self.hindsight.reflect_cognitive_shadow(days=days, user_id=user_id)
        insights = await self.hindsight.get_user_insights(user_id)
        memory_context = self._format_insights(insights)
        
        # Optionally use LLM to enhance the prediction text
        prediction_text = prediction.get("prediction", "Keep practicing consistently")
        recent_topics = prediction.get("recent_topics", [])
        
        if self.llm.available and recent_topics:
            # LLM enhances prediction only if we have real history
            topics_str = ", ".join(recent_topics[:3])
            prompt = f"""User history:
{memory_context}

Current question:
Refine shadow prediction for current learning path.

Instruction:
Adapt explanation based on user's past struggles.

Refine this prediction into a more engaging, actionable statement:

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
        
        result = {
            "feature": "cognitive_shadow",
            "response_id": response_id,
            "prediction": prediction_text,
            "confidence": prediction.get("confidence", 0.78),
            "evidence": prediction.get("evidence", []),
            "recent_topics": recent_topics,
            "demo_mode": prediction.get("demo_mode", True)
        }
        
        # ⚡ CRITICAL: Retain this interaction
        primary_topic = recent_topics[0] if recent_topics else "general"
        await self._retain_interaction(
            content=f"Shadow prediction for {primary_topic}",
            user_id=user_id,
            topic=primary_topic,
            engine_feature="shadow",
            interaction_data={
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "topics_count": len(recent_topics)
            }
        )
        
        return result
    
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
        insights = await self.hindsight.get_user_insights("anonymous")
        memory_context = self._format_insights(insights)

        prompt = f"""User history:
    {memory_context}

    Current question:
    Summarize learning patterns into one actionable insight.

    Instruction:
    Adapt explanation based on user's past struggles.

    Summarize these learning patterns into 1 actionable insight:
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