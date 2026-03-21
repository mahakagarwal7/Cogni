from typing import Any


class Orchestrator:
    """Simple rule-based engine selector.

    This class is additive and can be adopted incrementally by routes/services
    without changing existing pipeline behavior.
    """

    def decide_engine(self, query: str, insights: Any) -> str:
        if "struggle" in str(insights).lower():
            return "socratic"

        if "pattern" in query.lower():
            return "resonance"

        return "default"
