"""
👻 Feature 2: Socratic Ghost
A tutor that remembers every misconception you've ever had.

PHASE 9: Integrated with Killer Prompt Design for adaptive tutoring.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from app.services.prompt_template_service import prompt_template_service
from app.models.memory_types import Misconception
from typing import Dict, Any, List, Optional
import re

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

    def _concept_tokens(self, concept: str) -> List[str]:
        return [token for token in concept.lower().replace("_", " ").split() if len(token) > 2]

    def _extract_focus_terms(self, text: str, concept: str = "") -> List[str]:
        """Extract compact focus terms to keep follow-up questions tied to student response."""
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", text.lower())
        tokens = [tok.strip() for tok in cleaned.split() if len(tok.strip()) > 3]
        stopwords = {
            "this", "that", "with", "from", "about", "because", "there", "their", "would", "could",
            "should", "which", "where", "when", "what", "have", "has", "your", "into", "than",
            "then", "they", "them", "just", "very", "some", "more", "like", "also", "used",
            "using", "does", "dont", "know", "think", "seems", "seem", "much", "many",
        }
        concept_tokens = set(self._concept_tokens(concept))

        ordered_unique: List[str] = []
        for tok in tokens:
            if tok in stopwords:
                continue
            if tok in concept_tokens:
                continue
            if tok not in ordered_unique:
                ordered_unique.append(tok)
            if len(ordered_unique) >= 5:
                break
        return ordered_unique

    def _history_unresolved_focus(self, history: Dict[str, Any], concept: str) -> List[str]:
        """Extract unresolved misconception snippets for current concept from Socratic history."""
        rows = history.get("history") if isinstance(history, dict) else []
        if not isinstance(rows, list):
            return []

        concept_lower = concept.lower().strip()
        focus: List[str] = []
        for row in rows[:15]:
            if not isinstance(row, dict):
                continue
            row_text = " ".join(
                str(row.get(key, ""))
                for key in ["belief", "challenge_question", "content", "topic", "concept"]
            ).strip()
            if not row_text:
                continue
            outcome = str(row.get("outcome", "")).lower().strip()
            if outcome and outcome != "unresolved":
                continue
            if concept_lower and concept_lower not in row_text.lower() and not any(t in row_text.lower() for t in self._concept_tokens(concept_lower)):
                continue
            focus.append(row_text[:120])
            if len(focus) >= 3:
                break
        return focus

    def _normalize_question_text(self, question: str) -> str:
        cleaned = question.strip()
        cleaned = re.sub(r"^\*\*next question\*\*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^\*\*question\*\*:\s*", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _build_response_aware_fallback_followup(
        self,
        concept: str,
        user_response: str,
        previous_question: str,
        confusion_level: int,
    ) -> str:
        """Deterministic follow-up that references student's own answer focus."""
        response_terms = self._extract_focus_terms(user_response, concept)
        if response_terms:
            focus = response_terms[0]
            if confusion_level >= 4:
                return f"How does '{focus}' connect to the basic idea of {concept}?"
            if confusion_level >= 2:
                return f"What assumption about '{focus}' might fail in {concept}?"
            return f"Why is '{focus}' important when solving {concept} problems?"

        if previous_question:
            prev = self._normalize_question_text(previous_question)
            if prev:
                return f"Based on your answer, what part of {concept} is still unclear to you?"

        return self._build_followup_from_response(concept, user_response, confusion_level)

    def _is_topic_aligned(self, question: str, concept: str) -> bool:
        q = question.lower()
        concept_clean = concept.lower().strip()
        if not concept_clean:
            return True
        if concept_clean in q:
            return True
        tokens = self._concept_tokens(concept_clean)
        if not tokens:
            return True
        token_hits = sum(1 for token in tokens if token in q)
        return token_hits >= 1

    def _build_hindsight_topic_context(
        self,
        concept: str,
        history: Dict[str, Any],
        insights: List[Dict[str, Any]],
    ) -> str:
        """Build compact hindsight context focused on current concept."""
        concept_lower = concept.lower().strip()
        tokens = self._concept_tokens(concept_lower)

        relevant_history: List[str] = []
        history_rows = history.get("history") if isinstance(history, dict) else []
        if isinstance(history_rows, list):
            for row in history_rows[:10]:
                if not isinstance(row, dict):
                    continue
                row_text = " ".join(
                    str(row.get(key, ""))
                    for key in ["content", "belief", "challenge_question", "topic", "concept"]
                ).lower()
                if concept_lower in row_text or any(token in row_text for token in tokens):
                    belief = str(row.get("belief") or row.get("topic") or concept)
                    outcome = str(row.get("outcome", "unknown"))
                    relevant_history.append(f"- prior_belief={belief}; outcome={outcome}")
                if len(relevant_history) >= 3:
                    break

        relevant_insights: List[str] = []
        for row in insights[:10]:
            if not isinstance(row, dict):
                continue
            data = row.get("data") if isinstance(row.get("data"), dict) else {}
            topic = str(data.get("topic", "general"))
            issue = str(data.get("issue", "unclear_concept"))
            style = str(data.get("preferred_style", "guided"))
            topic_lower = topic.lower()
            if concept_lower in topic_lower or any(token in topic_lower for token in tokens):
                relevant_insights.append(f"- insight_topic={topic}; issue={issue}; style={style}")
            if len(relevant_insights) >= 3:
                break

        resolved_count = history.get("resolved_count", 0) if isinstance(history, dict) else 0
        unresolved_count = history.get("unresolved_count", 0) if isinstance(history, dict) else 0

        context_lines = [
            f"Concept focus: {concept}",
            f"Prior outcomes: resolved={resolved_count}, unresolved={unresolved_count}",
        ]
        if relevant_history:
            context_lines.append("Related history:")
            context_lines.extend(relevant_history)
        if relevant_insights:
            context_lines.append("Related insight patterns:")
            context_lines.extend(relevant_insights)

        return "\n".join(context_lines)

    def _enforce_topic_alignment(
        self,
        question: str,
        concept: str,
        user_belief: str,
        confusion_level: int,
        user_response: Optional[str] = None,
    ) -> str:
        """Deterministically force topic relevance when model output drifts."""
        clean_question = question.strip()
        if clean_question and self._is_topic_aligned(clean_question, concept):
            return clean_question if clean_question.endswith("?") else f"{clean_question}?"

        if user_response is not None:
            forced = self._build_followup_from_response(concept, user_response, confusion_level)
        else:
            forced = self._build_level_fallback_question(concept, user_belief, confusion_level)

        if not self._is_topic_aligned(forced, concept):
            forced = f"How does this idea apply to {concept} in one specific example?"
        return forced if forced.endswith("?") else f"{forced}?"

    def _build_hint(self, concept: str, question: str, confusion_level: int, response_type: str = "") -> str:
        """Generate a deterministic micro-hint without extra LLM calls."""
        if response_type in {"no_knowledge", "vague_response"} or confusion_level >= 4:
            return f"Start small: define one core property of {concept} in your own words."
        if response_type == "has_knowledge":
            return f"Use your prior idea and test it with one concrete {concept} example."
        if response_type == "detailed_response":
            return f"Good progress. Now test your reasoning against an edge case in {concept}."
        if question and question.lower().startswith("why"):
            return f"Focus on cause and effect: what changes in {concept} when your assumption changes?"
        if question and question.lower().startswith("how"):
            return f"Break it into steps: what is step one for solving this in {concept}?"
        return f"Anchor your answer in one specific example related to {concept}."

    def analyzeResponse(self, response: str) -> Dict[str, Any]:
        """Modular adaptive response analysis for Socratic loop."""
        response_type = self._classify_response(response)
        analysis_text = self._analyze_response(response)
        score_map = {
            "no_knowledge": 0.2,
            "vague_response": 0.35,
            "has_knowledge": 0.65,
            "detailed_response": 0.8,
        }
        understanding_score = score_map.get(response_type, 0.5)
        return {
            "response_type": response_type,
            "analysis": analysis_text,
            "understanding_score": understanding_score,
            "needs_hint": response_type in {"no_knowledge", "vague_response"},
            "is_progressing": response_type in {"has_knowledge", "detailed_response"},
        }

    async def updateLearningState(
        self,
        concept: str,
        user_id: str,
        response_analysis: Dict[str, Any],
        previous_question: str = "",
        user_response: str = "",
    ) -> Dict[str, Any]:
        """Persist adaptive learning state to memory and return summarized state."""
        response_type = str(response_analysis.get("response_type", "vague_response"))
        understanding_score = float(response_analysis.get("understanding_score", 0.5))

        if response_type in {"has_knowledge", "detailed_response"}:
            outcome = "resolved"
            learning_state = "progressing"
        elif response_type == "no_knowledge":
            outcome = "unresolved"
            learning_state = "foundational_gap"
        else:
            outcome = "unresolved"
            learning_state = "needs_clarification"

        await self._retain_interaction(
            content=f"Adaptive Socratic state update for {concept}",
            user_id=user_id,
            topic=concept,
            engine_feature="socratic_learning_state",
            interaction_data={
                "previous_question": previous_question,
                "user_response": user_response,
                "response_type": response_type,
                "understanding_score": understanding_score,
                "outcome": outcome,
                "learning_state": learning_state,
            },
        )

        return {
            "outcome": outcome,
            "learning_state": learning_state,
            "understanding_score": understanding_score,
            "response_type": response_type,
        }

    async def generateQuestion(
        self,
        context: Dict[str, Any],
        hindsightData: Dict[str, Any],
        userResponse: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate adaptive Socratic question with optional response-aware follow-up."""
        concept = str(context.get("concept", "the topic")).strip() or "the topic"
        user_belief = str(context.get("user_belief", "")).strip()
        confusion_level = int(context.get("confusion_level", 3) or 3)
        user_id = str(context.get("user_id", "anonymous"))
        previous_question = str(context.get("previous_question", "")).strip()

        history = hindsightData.get("history") if isinstance(hindsightData.get("history"), dict) else {}
        insights = hindsightData.get("insights") if isinstance(hindsightData.get("insights"), list) else []
        memory_context = self._build_hindsight_topic_context(concept, history, insights)
        style_instruction = self._get_socratic_style(confusion_level)
        unresolved_focus = self._history_unresolved_focus(history, concept)

        response_analysis: Optional[Dict[str, Any]] = None
        if userResponse is not None:
            response_analysis = self.analyzeResponse(userResponse)
            analysis_text = str(response_analysis.get("analysis", "Student response needs probing."))
            response_type = str(response_analysis.get("response_type", "vague_response"))
            response_terms = self._extract_focus_terms(userResponse, concept)
            response_terms_text = ", ".join(response_terms[:3]) if response_terms else "none"
            unresolved_text = " | ".join(unresolved_focus) if unresolved_focus else "none"
            query = (
                f"The student is learning {concept}. "
                f"Previous question: '{previous_question}'. "
                f"Student response: '{userResponse}'. "
                f"Response type: {response_type}. "
                f"Analysis: {analysis_text}. "
                f"Response focus terms: {response_terms_text}. "
                f"Unresolved memory focus: {unresolved_text}. "
                f"Ask the NEXT Socratic question under 20 words, starting with What/How/Why. "
                f"{style_instruction}"
            )
        else:
            is_vague = self._is_vague_belief(user_belief)
            if is_vague:
                query = (
                    f"The student is unsure about {concept}. "
                    f"Ask a Socratic question to discover prior knowledge (What/How/Can you, under 20 words). "
                    f"{style_instruction}"
                )
            else:
                query = (
                    f"Student believes: '{user_belief}' about {concept}. "
                    f"Ask a Socratic question to test this belief (What/How/Why, under 20 words). "
                    f"{style_instruction}"
                )

        prompt_seed = await prompt_template_service.generate_adaptive_prompt(
            user_id=user_id,
            query=query,
            topic=concept,
        )

        prompt = f"""{prompt_seed}

MEMORY SIGNALS:
{memory_context}

DIFFICULTY ADAPTATION:
Confusion level: {confusion_level}/5
Style rule: {style_instruction}

SPECIFIC INSTRUCTION FOR THIS RESPONSE:
Question must be explicitly about {concept} and mention {concept} or a direct property of it.
If student response exists, the question must connect to at least one response focus term.
Return ONLY a JSON object with a "question" key containing the Socratic question.
Format: {{"question": "Your question here?"}}"""

        question = ""
        if self.llm.available:
            try:
                response = self.llm.generate(prompt, max_tokens=100, temperature=0.35)
                question = self._extract_question_from_response(response)
            except Exception:
                question = ""

        if not question:
            if userResponse is not None:
                question = self._build_followup_from_response(concept, userResponse, confusion_level)
            else:
                question = self._build_level_fallback_question(concept, user_belief, confusion_level)

        question_lower = question.lower()
        meta_markers = ["the student", "the goal is", "i need to", "socratic question to"]
        if any(marker in question_lower for marker in meta_markers):
            if userResponse is not None:
                question = self._build_followup_from_response(concept, userResponse, confusion_level)
            else:
                question = self._build_level_fallback_question(concept, user_belief, confusion_level)

        question = self._enforce_topic_alignment(
            question=question,
            concept=concept,
            user_belief=user_belief,
            confusion_level=confusion_level,
            user_response=userResponse,
        )

        # For reflection turns, enforce anchoring to student's own response signals.
        if userResponse is not None:
            response_terms = self._extract_focus_terms(userResponse, concept)
            if response_terms:
                q_lower = question.lower()
                anchored = any(term in q_lower for term in response_terms[:3])
                if not anchored:
                    question = self._build_response_aware_fallback_followup(
                        concept=concept,
                        user_response=userResponse,
                        previous_question=previous_question,
                        confusion_level=confusion_level,
                    )
                    question = self._enforce_topic_alignment(
                        question=question,
                        concept=concept,
                        user_belief=user_belief,
                        confusion_level=confusion_level,
                        user_response=userResponse,
                    )

        hint = self._build_hint(
            concept=concept,
            question=question,
            confusion_level=confusion_level,
            response_type=str(response_analysis.get("response_type", "")) if response_analysis else "",
        )

        return {
            "question": question,
            "hint": hint,
            "response_analysis": response_analysis,
        }

    async def get_hint(
        self,
        concept: str,
        previous_question: str,
        user_id: str = "anonymous",
        confusion_level: int = 3,
        user_response: str = "",
    ) -> Dict[str, Any]:
        """Return a micro-hint for current Socratic turn without an extra LLM call."""
        analysis = self.analyzeResponse(user_response) if user_response.strip() else {"response_type": ""}
        hint = self._build_hint(
            concept=concept,
            question=previous_question,
            confusion_level=confusion_level,
            response_type=str(analysis.get("response_type", "")),
        )

        await self._retain_interaction(
            content=f"Socratic hint requested for {concept}",
            user_id=user_id,
            topic=concept,
            engine_feature="socratic_hint",
            interaction_data={
                "previous_question": previous_question,
                "hint": hint,
                "confusion_level": confusion_level,
            },
        )

        return {
            "feature": "socratic_hint",
            "concept": concept,
            "previous_question": previous_question,
            "hint": hint,
            "confidence": self._get_default_confidence(),
            "demo_mode": not self.llm.available,
        }
    
    async def ask_socratic_question(self, concept: str, user_belief: str, user_id: str = "anonymous", confusion_level: int = 3) -> Dict[str, Any]:
        """
        Ask a Socratic question based on past misconceptions using Groq LLM.
        Now enhanced with PHASE 9 Killer Prompt Design for adaptive tutoring.
        
        CRITICAL: Automatically retains interaction to hindsight memory for future recall.
        """
        # Get past dialogue history
        history = await self.hindsight.recall_socratic_history(concept, user_id=user_id)
        insights = await self.hindsight.get_user_insights(user_id)
        
        question_payload = await self.generateQuestion(
            context={
                "concept": concept,
                "user_belief": user_belief,
                "confusion_level": confusion_level,
                "user_id": user_id,
            },
            hindsightData={"history": history, "insights": insights},
        )
        question = str(question_payload.get("question", "")).strip() or self._build_level_fallback_question(concept, user_belief, confusion_level)
        hint = str(question_payload.get("hint", "")).strip()
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
            "hint": hint,
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
        previous_question = self._normalize_question_text(previous_question)

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
        
        # STEP 3: Reflect - generate adaptive follow-up and micro-hint
        question_payload = await self.generateQuestion(
            context={
                "concept": concept,
                "confusion_level": confusion_level,
                "user_id": user_id,
                "previous_question": previous_question,
            },
            hindsightData={"history": history, "insights": insights},
            userResponse=user_response,
        )
        follow_up_question = str(question_payload.get("question", "")).strip()
        if not follow_up_question:
            follow_up_question = self._build_followup_from_response(concept, user_response, confusion_level)

        response_analysis_data = question_payload.get("response_analysis")
        if isinstance(response_analysis_data, dict):
            response_analysis = str(response_analysis_data.get("analysis", self._analyze_response(user_response)))
        else:
            response_analysis = self._analyze_response(user_response)
        hint = str(question_payload.get("hint", "")).strip()

        learning_state = await self.updateLearningState(
            concept=concept,
            user_id=user_id,
            response_analysis=self.analyzeResponse(user_response),
            previous_question=previous_question,
            user_response=user_response,
        )
        
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
            "hint": hint,
            "learning_state": learning_state.get("learning_state"),
            "understanding_score": learning_state.get("understanding_score"),
            "confusion_level": confusion_level,
            "confidence": self._get_default_confidence(),
            "demo_mode": not self.llm.available  # ONLY demo if LLM itself is unavailable, not based on history
        }

        response_type = str(learning_state.get("response_type", self._classify_response(user_response)))
        outcome = str(learning_state.get("outcome", "unresolved"))
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