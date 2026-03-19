"""
👻 Feature 2: Socratic Ghost
A tutor that remembers every misconception you've ever had.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from app.models.memory_types import Misconception
from typing import Dict, Any, List

class SocraticEngine:
    """
    Socratic Ghost Engine - Persistent dialogue with memory.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
        self.llm = llm_service
    
    def _get_default_confidence(self) -> float:
        """Default confidence for Socratic questioning."""
        return 0.85
    
    async def ask_socratic_question(self, concept: str, user_belief: str) -> Dict[str, Any]:
        """
        Ask a Socratic question based on past misconceptions using Groq LLM.
        """
        # Get past dialogue history
        history = await self.hindsight.recall_socratic_history(concept)
        
        # Use Groq LLM to generate personalized Socratic question
        context = f"Student believes: '{user_belief}' about {concept}."
        if history.get("unresolved_count", 0) > 0:
            context += f" They've struggled with this before."
        
        prompt = f"""INSTRUCTION: You MUST respond with ONLY a JSON object. No thinking, no explanation.

{{"question": "A Socratic question to challenge: {context}"}}

Just return valid JSON with the key 'question' containing a challenging Socratic question (starts with What/How/Why, under 20 words).
Response format (copy and fill): {{"question": "?"}}"""
        
        response = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
        
        question = "Can you think of a simpler case or alternative approach?"
        
        # Debug: log raw response
        print(f"[DEBUG] Raw response (first 250 chars): {repr(response[:250])}")
        
        # Aggressive cleanup: skip thinking, find JSON
        try:
            # Remove <think> tags completely
            cleaned = response.replace("<think>", "").replace("</think>", "")
            
            # Find JSON object - look for { ... }
            json_match = None
            brace_count = 0
            in_json = False
            start_pos = -1
            
            for i, char in enumerate(cleaned):
                if char == "{":
                    if not in_json:
                        start_pos = i
                        in_json = True
                        brace_count = 1
                    else:
                        brace_count += 1
                elif char == "}" and in_json:
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = cleaned[start_pos:i+1]
                        try:
                            import json
                            parsed = json.loads(json_str)
                            if "question" in parsed:
                                question = str(parsed["question"]).strip()
                                if question and not question.endswith("?"):
                                    question = question + "?"
                                break
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"[WARNING] Error extracting JSON: {e}")
        
        print(f"[DEBUG] Final question: {repr(question)}")
        
        return {
            "feature": "socratic_ghost",
            "concept": concept,
            "user_belief": user_belief,
            "question": question,
            "confidence": self._get_default_confidence(),
            "past_history": history,
            "demo_mode": history.get("demo_mode", True) and not self.llm.available
        }
    
    async def log_misconception(self, misconception: Misconception) -> Dict[str, Any]:
        """
        Save a misconception to memory.
        """
        content = f"Misconception: {misconception.concept} - '{misconception.incorrect_belief}'"
        
        result = await self.hindsight.retain_misconception(
            content=content,
            context=misconception.model_dump()
        )
        
        return {
            "feature": "misconception_log",
            "status": result.get("status"),
            "misconception": misconception.model_dump(),
            "demo_mode": result.get("demo_mode", True)
        }
    
    async def get_dialogue_history(self, concept: str) -> Dict[str, Any]:
        """
        Get all past dialogues about a concept.
        """
        history = await self.hindsight.recall_socratic_history(concept)
        
        return {
            "feature": "dialogue_history",
            "concept": concept,
            "total_found": history.get("total_found", 0),
            "resolved_count": history.get("resolved_count", 0),
            "unresolved_count": history.get("unresolved_count", 0),
            "history": history.get("history", []),
            "demo_mode": history.get("demo_mode", True)
        }