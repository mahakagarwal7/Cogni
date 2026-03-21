"""
👻 Feature 2: Socratic Ghost
A tutor that remembers every misconception you've ever had.

PHASE 9: Integrated with Killer Prompt Design for adaptive tutoring.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from app.services.prompt_template_service import prompt_template_service
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

    def _get_socratic_style(self, confusion_level: int) -> str:
        """Return question-style instruction based on confusion level (1-5)."""
        if confusion_level >= 5:
            return "Use very simple language, concrete everyday examples, and one-step reasoning."
        if confusion_level == 4:
            return "Use simple language and ask about one core idea only."
        if confusion_level == 3:
            return "Use balanced language and test one key assumption."
        if confusion_level == 2:
            return "Use technical wording and probe causal reasoning."
        return "Use precise technical wording and challenge deeper abstraction or edge cases."

    def _is_vague_belief(self, user_belief: str) -> bool:
        """Detect if user_belief is too generic to work with."""
        belief_lower = user_belief.strip().lower()
        vague_patterns = [
            "don't know", "dont know", "unclear", "confused", "not sure",
            "don't understand", "dont understand", "nothing", "no idea",
            "i don't know", "i dont know", "???", "help", "idk",
            "can't understand", "cant understand", "lost", "stuck"
        ]
        return any(pattern in belief_lower for pattern in vague_patterns)
    
    def _build_level_fallback_question(self, concept: str, user_belief: str, confusion_level: int) -> str:
        """Fallback Socratic question that still adapts to confusion level."""
        # If belief is vague, ask about their existing knowledge instead
        if self._is_vague_belief(user_belief):
            if confusion_level >= 5:
                return f"Can you describe one thing you DO know about {concept}?"
            if confusion_level == 4:
                return f"What comes to mind first when you think of {concept}?"
            if confusion_level == 3:
                return f"What have you heard or seen about {concept} before?"
            if confusion_level == 2:
                return f"What properties or characteristics does {concept} have?"
            return f"What would you need to understand about {concept} before you could solve a problem with it?"
        
        # Normal fallback for specific beliefs
        if confusion_level >= 5:
            return f"What simple real-life example of {concept} makes '{user_belief}' seem true?"
        if confusion_level == 4:
            return f"Why does '{user_belief}' about {concept} seem correct at first?"
        if confusion_level == 3:
            return f"What assumption about {concept} makes '{user_belief}' seem true?"
        if confusion_level == 2:
            return f"How could '{user_belief}' about {concept} fail in a specific case?"
        return f"What exception or edge case would disprove '{user_belief}'?"
    
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
    
    async def ask_socratic_question(self, concept: str, user_belief: str, user_id: str = "anonymous", confusion_level: int = 3) -> Dict[str, Any]:
        """
        Ask a Socratic question based on past misconceptions using Groq LLM.
        Now enhanced with PHASE 9 Killer Prompt Design for adaptive tutoring.
        
        CRITICAL: Automatically retains interaction to hindsight memory for future recall.
        """
        # Get past dialogue history
        history = await self.hindsight.recall_socratic_history(concept, user_id=user_id)
        insights = await self.hindsight.get_user_insights(user_id)
        memory_context = self._format_insights(insights)
        
        # Check if belief is too vague - handle specially
        is_vague = self._is_vague_belief(user_belief)
        
        # PHASE 9: Generate killer prompt with adaptive rules
        style_instruction = self._get_socratic_style(confusion_level)
        
        if is_vague:
            # For vague beliefs, ask about their existing knowledge
            query = (f"The student is unsure about {concept}. "
                    f"Ask a Socratic question to find out what they already know about {concept} "
                    f"(starts with What/How/Can you, under 20 words). {style_instruction}")
        else:
            # For specific beliefs, probe the misconception
            query = (f"Student believes: '{user_belief}' about {concept}. "
                    f"Ask a Socratic question to test this belief (starts with What/How/Why, under 20 words). "
                    f"{style_instruction}")

        killer_prompt = await prompt_template_service.generate_adaptive_prompt(
            user_id=user_id,
            query=query,
            topic=concept
        )
        
        # Build prompt with killer template
        prompt = f"""{killer_prompt}

    DIFFICULTY ADAPTATION:
    Confusion level: {confusion_level}/5
    Style rule: {style_instruction}

SPECIFIC INSTRUCTION FOR THIS RESPONSE:
Return ONLY a JSON object with a "question" key containing the Socratic question.
Format: {{"question": "Your question here?"}}"""
        
        response = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
        default_question = "Can you think of a simpler case or alternative approach?"
        
        question = ""
        
        # Debug: log raw response
        print(f"[DEBUG] Raw response (first 250 chars): {repr(response[:250])}")
        
        # Aggressive cleanup: skip thinking, find JSON first
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

            # If JSON parsing didn't produce a question, fall back to first sensible line/question.
            if not question:
                cleaned_lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
                for ln in cleaned_lines:
                    low = ln.lower()
                    if low.startswith("{") or low.startswith("}"):
                        continue
                    if low.startswith("question:"):
                        ln = ln.split(":", 1)[1].strip()
                    if len(ln) < 8:
                        continue
                    if ln.endswith("?"):
                        question = ln
                        break
                if not question and cleaned_lines:
                    candidate = cleaned_lines[0]
                    if candidate.lower().startswith("question:"):
                        candidate = candidate.split(":", 1)[1].strip()
                    candidate = candidate.strip('"\'')
                    if candidate:
                        question = candidate if candidate.endswith("?") else f"{candidate}?"
        except Exception as e:
            print(f"[WARNING] Error extracting JSON: {e}")

        if not question:
            question = self._build_level_fallback_question(concept, user_belief, confusion_level)

        # If the result is still generic, run one focused second pass to force a topic-specific question.
        if question.strip().lower() == default_question.lower() and self.llm.available:
            if is_vague:
                second_prompt = f"""Write ONE Socratic question to find out what the student knows about {concept}.
Rules:
- Must start with What, Can you, or How
- Must be specific to {concept}, not generic
- Must be under 18 words
- Return ONLY the question text
- Examples: "What is one property of {concept}?", "Can you name a use of {concept}?"
- Confusion level is {confusion_level}/5. {style_instruction}
"""
            else:
                second_prompt = f"""Write ONE Socratic question about {concept} based on the student's belief: {user_belief}.

Rules:
- Must start with What, Why, or How
- Must mention {concept}
- Max 18 words
- Return ONLY the question text
- Do NOT use: 'Can you think of a simpler case or alternative approach?'
- Confusion level is {confusion_level}/5. {style_instruction}
"""
            try:
                second = self.llm.generate(second_prompt, max_tokens=60, temperature=0.4)
                second_clean = second.replace("<think>", "").replace("</think>", "").strip()

                # Prefer first explicit question sentence from model output.
                candidates = []
                for part in second_clean.replace("\n", " ").split("?"):
                    p = part.strip().strip('"\'')
                    if not p:
                        continue
                    p = f"{p}?"
                    lower = p.lower()
                    if lower.startswith(("what", "why", "how")):
                        candidates.append(p)

                # If model didn't return a clean question, synthesize one.
                if candidates:
                    second_clean = candidates[0]
                else:
                    second_clean = self._build_level_fallback_question(concept, user_belief, confusion_level)

                if concept.lower() in second_clean.lower() and second_clean.lower() != default_question.lower():
                    question = second_clean
            except Exception:
                pass
        
        # Guardrail: reject meta/planning text that sometimes slips through.
        meta_markers = [
            "the student",
            "learning history",
            "foundational",
            "the goal is",
            "socratic question to",
            "i need to",
            "okay,",
        ]
        q_lower = question.lower()
        if any(marker in q_lower for marker in meta_markers):
            question = self._build_level_fallback_question(concept, user_belief, confusion_level)

        # If model keeps returning the same generic medium-level pattern,
        # rewrite it to the requested difficulty level.
        if confusion_level != 3 and question.lower().startswith("what assumption about"):
            question = self._build_level_fallback_question(concept, user_belief, confusion_level)

        print(f"[DEBUG] Final question: {repr(question)}")
        
        # BUILD response object
        from uuid import uuid4
        
        response_id = str(uuid4())
        result = {
            "response_id": response_id,
            "feature": "socratic_ghost",
            "concept": concept,
            "user_belief": user_belief,
            "confusion_level": confusion_level,
            "question": question,
            "confidence": self._get_default_confidence(),
            "past_history": history,
            "demo_mode": not self.llm.available  # ONLY demo if LLM itself is unavailable
        }
        
        # ⚡ CRITICAL: Retain this interaction to hindsight for future recalls
        # This creates memory nodes for every new topic/user combination
        await self._retain_interaction(
            content=f"Socratic question about {concept}",
            user_id=user_id,
            topic=concept,
            engine_feature="socratic",
            interaction_data={
                "user_belief": user_belief,
                "question": question,
                "confidence": result["confidence"]
            }
        )

        # Close the learning loop with explicit belief/challenge/outcome memory signal.
        await self._retain_interaction(
            content=(
                f"Student believed '{user_belief}' about {concept}. "
                f"Challenged with: '{question}'. Outcome: unresolved"
            ),
            user_id=user_id,
            topic=concept,
            engine_feature="socratic_outcome",
            interaction_data={
                "belief": user_belief,
                "challenge_question": question,
                "outcome": "unresolved",
            }
        )
        
        return result
    
    async def reflect_on_response(
        self,
        concept: str,
        user_response: str,
        user_id: str = "anonymous",
        previous_question: str = "",
        confusion_level: int = 3
    ) -> Dict[str, Any]:
        """
        Reflect on user's response to a Socratic question and generate a better follow-up.
        
        This implements the CORE Hindsight feedback loop:
        1. Retain: User response is saved to memory
        2. Recall: Previous interactions & confusion patterns are retrieved
        3. Reflect: Better follow-up question is generated based on response
        """
        # STEP 1: Retain the user's response
        await self._retain_interaction(
            content=f"User response to Socratic question about {concept}",
            user_id=user_id,
            topic=concept,
            engine_feature="socratic_reflection",
            interaction_data={
                "previous_question": previous_question,
                "user_response": user_response,
                "response_type": self._classify_response(user_response)
            }
        )
        
        # STEP 2: Recall all past interactions for this topic
        history = await self.hindsight.recall_socratic_history(concept, user_id=user_id)
        insights = await self.hindsight.get_user_insights(user_id)
        
        # STEP 3: Reflect - generate a BETTER follow-up based on response
        style_instruction = self._get_socratic_style(confusion_level)
        
        response_analysis = self._analyze_response(user_response)
        
        reflect_prompt = await prompt_template_service.generate_adaptive_prompt(
            user_id=user_id,
            query=(
                f"The student is learning about {concept}.\n"
                f"Previous question: '{previous_question}'\n"
                f"Student's response: '{user_response}'\n"
                f"Response analysis: {response_analysis}\n"
                f"Generate the NEXT Socratic question that:\n"
                f"- Builds on their response\n"
                f"- Is more specific and targeted\n"
                f"- Addresses gaps in their understanding\n"
                f"- Is under 20 words\n"
                f"- Starts with What/How/Why\n"
                f"{style_instruction}"
            ),
            topic=concept
        )
        
        prompt = f"""{reflect_prompt}

    DIFFICULTY ADAPTATION:
    Confusion level: {confusion_level}/5
    Style rule: {style_instruction}

SPECIFIC INSTRUCTION FOR THIS RESPONSE:
Return ONLY a JSON object with a "question" key containing the next Socratic question.
Format: {{"question": "Your follow-up question here?"}}"""
        
        response = self.llm.generate(prompt, max_tokens=100, temperature=0.35)
        follow_up_question = self._extract_question_from_response(response)
        
        if not follow_up_question:
            # Fallback: generate question based on response type
            follow_up_question = self._build_followup_from_response(concept, user_response, confusion_level)
        
        from uuid import uuid4
        response_id = str(uuid4())
        result = {
            "response_id": response_id,
            "feature": "socratic_reflection",
            "concept": concept,
            "previous_question": previous_question,
            "user_response": user_response,
            "response_analysis": response_analysis,
            "follow_up_question": follow_up_question,
            "confusion_level": confusion_level,
            "confidence": self._get_default_confidence(),
            "demo_mode": not self.llm.available  # ONLY demo if LLM itself is unavailable, not based on history
        }

        response_type = self._classify_response(user_response)
        outcome = "resolved" if response_type in {"has_knowledge", "detailed_response"} else "unresolved"
        await self._retain_interaction(
            content=(
                f"Student believed '{concept}' misconception and responded '{user_response}'. "
                f"Challenged with: '{previous_question}'. Outcome: {outcome}"
            ),
            user_id=user_id,
            topic=concept,
            engine_feature="socratic_outcome",
            interaction_data={
                "belief": concept,
                "challenge_question": previous_question,
                "outcome": outcome,
                "response_type": response_type,
            }
        )
        
        return result
    
    def _classify_response(self, response: str) -> str:
        """Classify the type of response (vague, specific, negative, positive, etc)."""
        lower = response.strip().lower()
        
        if not lower or lower in ["nothing", "no", "n/a", "???", "idk", "i don't know"]:
            return "no_knowledge"
        if any(word in lower for word in ["yes", "i know", "have", "i've"]):
            return "has_knowledge"
        if any(len(word) > 3 for word in lower.split()):  # Multi-word or detailed
            return "detailed_response"
        return "vague_response"
    
    def _analyze_response(self, response: str) -> str:
        """Analyze what the response tells us about the student."""
        response_type = self._classify_response(response)
        
        if response_type == "no_knowledge":
            return "Student has NO prior knowledge. Need to introduce basic concepts."
        elif response_type == "has_knowledge":
            return "Student has SOME knowledge. Can build on existing understanding."
        elif response_type == "detailed_response":
            return "Student provided DETAILED response. Can probe deeper into specifics."
        else:
            return "Student provided VAGUE response. Need to make concepts more concrete."
    
    def _extract_question_from_response(self, response: str) -> str:
        """Extract the follow-up question from LLM response."""
        try:
            cleaned = response.replace("<think>", "").replace("</think>", "").strip()
            
            # Try JSON extraction
            import json
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
                            parsed = json.loads(json_str)
                            question = str(parsed.get("question", "")).strip()
                            if question and not question.endswith("?"):
                                question = question + "?"
                            if question:
                                return question
                        except json.JSONDecodeError:
                            pass
            
            # Try text extraction
            for line in cleaned.splitlines():
                line = line.strip()
                if line.endswith("?") and len(line) > 8:
                    return line
        except Exception:
            pass
        
        return ""
    
    def _build_followup_from_response(self, concept: str, user_response: str, confusion_level: int) -> str:
        """Build a follow-up question based on response classification."""
        response_type = self._classify_response(user_response)
        
        if response_type == "no_knowledge":
            # User has no knowledge - start with concrete basics
            if confusion_level >= 5:
                return f"Can you think of a situation where {concept} might matter?"
            if confusion_level >= 3:
                return f"Where do you think {concept} is used in real life?"
            return f"What would be a simple scenario to understand {concept}?"
        
        elif response_type == "has_knowledge":
            # User has some knowledge - probe deeper
            if confusion_level >= 5:
                return f"Why is that property of {concept} important?"
            if confusion_level >= 3:
                return f"How does that relate to other aspects of {concept}?"
            return f"What are the implications of that for {concept}?"
        
        elif response_type == "detailed_response":
            # User gave detailed response - dig into specifics
            if confusion_level >= 5:
                return f"Can you give an example of that in {concept}?"
            if confusion_level >= 3:
                return f"How would you apply that to a specific {concept} problem?"
            return f"What would happen if that changed in {concept}?"
        
        else:
            # Vague response - make it concrete
            if confusion_level >= 5:
                return f"Can you describe ONE specific thing about {concept}?"
            if confusion_level >= 3:
                return f"What is the simplest part of {concept} you can think of?"
            return f"What is the core principle of {concept}?"
    
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
            "demo_mode": history.get("demo_mode", False)  # Changed default to False - use local fallback
        }