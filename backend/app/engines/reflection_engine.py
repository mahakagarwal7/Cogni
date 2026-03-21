# backend/app/engines/reflection_engine.py
from typing import Any, Dict, List


class ReflectionEngine:
    """
    Lightweight rule-based reflection engine.

    This is intentionally deterministic and additive so it can improve
    insight quality without changing the existing pipeline behavior.
    """

    def analyze(self, interaction: Dict[str, Any], feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []

        if not feedback["understood"]:
            insights.append(
                {
                    "topic": self.extract_topic(interaction["query"]),
                    "issue": "concept_not_clear",
                    "preferred_style": "simpler_explanation",
                }
            )

        if feedback["confidence"] < 0.5:
            insights.append(
                {
                    "issue": "low_confidence",
                    "action": "add_examples",
                }
            )

        return insights

    def extract_topic(self, query: str) -> str:
        # Simple keyword extraction; can be upgraded with LLM later.
        q = query.lower()
        if "recursion" in q:
            return "recursion"
        return "general"


reflection_engine = ReflectionEngine()
