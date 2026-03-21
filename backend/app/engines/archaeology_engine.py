# backend/app/engines/archaeology_engine.py
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from app.models.memory_types import StudySession
from typing import Dict, Any, List

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
    
    def _build_explanation_prompt(self, topic: str, confusion_level: int) -> tuple[str, str]:
        """
        Build adaptive explanation prompt based on confusion level.
        Returns (prompt, target_audience) tuple.
        """
        audience_mapping = {
            5: ("a 5-year-old using simple analogies and stories", "5-year-old"),
            4: ("a middle school student (grades 5-6)", "middle_school"),
            3: ("a high school student", "high_school"),
            2: ("a JEE/NEET aspirant (competitive exam level)", "competitive_exam"),
            1: ("an undergraduate student with technical precision", "undergraduate"),
        }
        
        target_level, audience_type = audience_mapping.get(confusion_level, audience_mapping[3])
        
        prompt = f"""Explain the concept of "{topic}" in a way suitable for {target_level}.

Requirements:
* Write 4 to 5 comprehensive paragraphs
* Use clear, engaging language appropriate for the audience
* Include relevant examples and intuitive comparisons
* Avoid meta-explanations like "let me explain" or "I'll now discuss"
* Do NOT use bullet points or numbered lists
* Do NOT include ANY planning text, instructions, or meta-commentary (like "use this example", "mention that", "avoid this term", "make sure to", "would be good", "could work", "need to mention")
* Focus ONLY on the educational content itself, not on HOW to structure or deliver it
* Do not include sentences starting with: "Then", "Next", "After", "Also,", "So,", "But", "Or", "And", "First", "Second", "Third", "Make sure", "Ensure", "Use words", "Avoid technical", "The key", "This is important", "One more thing"
* If a sentence talks about how to explain something rather than explaining it, remove it
* Make it engaging and clear with complete, detailed information

Begin the explanation directly without any preamble. Only include the actual explanation content."""

        return prompt, audience_type
    
    def _clean_explanation_text(self, text: str) -> str:
        """
        Aggressively clean LLM explanation output.
        Removes thinking patterns, meta-reasoning, and hedging language throughout.
        Preserves only pure explanatory content and ensures complete sentences.
        """
        cleaned = text.strip()
        
        # Step 1: Remove thinking tags
        if "<think>" in cleaned:
            parts = cleaned.split("</think>", 1)
            if len(parts) > 1:
                cleaned = parts[-1].strip()
            else:
                cleaned = cleaned.split("<think>", 1)[-1].strip()
        
        # Step 2: Remove leading markdown and meta-openers
        cleaned = cleaned.lstrip("\n*#- ").strip()
        
        # Step 3: Split into sentences and filter out thinking patterns
        sentences = []
        current_sentence = ""
        
        for char in cleaned:
            current_sentence += char
            if char in ".!?":
                sentence = current_sentence.strip()
                
                # Check if this sentence contains thinking patterns
                is_thinking = self._is_thinking_sentence(sentence)
                
                if not is_thinking and sentence:
                    sentences.append(sentence)
                
                current_sentence = ""
        
        # Add any remaining partial sentence only if it's substantial
        if current_sentence.strip():
            sentence = current_sentence.strip()
            if not self._is_thinking_sentence(sentence) and len(sentence) > 20:
                # Only add if it doesn't look truncated (ends with reasonable punctuation or word)
                if not sentence.endswith(","):
                    sentences.append(sentence)
        
        # Step 4: Join sentences and ensure we have content
        result = " ".join(sentences).strip()
        
        # Step 5: Ensure result ends with proper punctuation
        if result and result[-1] not in ".!?":
            # Find the last complete sentence
            for i in range(len(result) - 1, -1, -1):
                if result[i] in ".!?":
                    result = result[:i+1]
                    break
        
        # If we filtered out everything, reconstruct from original with proper boundaries
        if not result:
            # Try to get at least some complete sentences from the original
            original_sentences = []
            current = ""
            for char in cleaned:
                current += char
                if char in ".!?":
                    sentence = current.strip()
                    if len(sentence) > 10:
                        original_sentences.append(sentence)
                    current = ""
            # Use first few complete sentences if filtering removed everything
            result = " ".join(original_sentences[:4]).strip()
            if not result:
                result = cleaned[:600]  # Last resort: grab first 600 chars if still empty
        
        return result
    
    def _is_thinking_sentence(self, sentence: str) -> bool:
        """
        Detect if a sentence is thinking/meta-reasoning rather than content.
        Returns True if sentence should be filtered out.
        """
        s = sentence.lower()
        
        # Thinking starters
        thinking_starts = [
            "wait,", "hmm,", "maybe", "perhaps", "let me ", "i think", 
            "i should", "i need to", "okay,", "alright,", "let's",
            "first,", "so i", "actually,", "but wait", "but how", 
            "but i", "but maybe", "another ", "also maybe", "but the",
            "or maybe", "or perhaps",  # Thinking about alternatives
            "no, maybe",  # Reconsidering/changing mind
            "alternatively, maybe",  # Tentative alternatives
            "so maybe",  # Thinking about examples
            "let me think", "let me start by recalling", "i should define",
            "i need to make", "i should use", "i can", "i could",
            "here's", "here is", "one example", "another example",
            "for instance", "such as", "like", "for example",
            "wait, right", "right, like", "so,", "thus,", "therefore,",
            "in conclusion", "to summarize", "in summary", "in short",
            "no,",  # Simple disagreement/reconsideration
        ]
        
        # Check if sentence starts with thinking patterns
        for start in thinking_starts:
            if s.startswith(start):
                return True
        
        # Filter out hedging/uncertainty phrases characteristic of thinking
        hedging_patterns = [
            "but wait,",
            "but how",
            "maybe better",
            "maybe avoid",
            "better to focus",
            "maybe i should",
            "i'm not sure",
            "i should stick",
            "hmm, maybe",
            "no, wait",
            "wait, i",
            "but i",
            "or is it",
            "wait, is it",
            "need to be careful",
            "let me clarify",
            "actually,",
            "wait, right,",
            "no, that's",
            "hmm, actually",
            "also, maybe",  # Thinking hedging pattern
            "not sure",  # Uncertain thinking
            "maybe helps",  # Tentative examples
            "maybe the",  # Tentative suggestions
            "maybe too",  # Uncertain assessments
            "but maybe",  # Conflicted thinking
        ]
        
        for pattern in hedging_patterns:
            if pattern in s:
                return True
        
        # Filter out meta-reasoning about what to include
        meta_patterns = [
            "might be confusing",
            "might not be",
            "probably shouldn't",
            "should avoid",
            "focus on the",
            "stick to",
            "don't mention",
            "avoid that",
            "make sure to",
            "use that as",
            "as the",
            "might have studied",
            "maybe describe",  # Meta-instructions
            "maybe how",  # Meta-instructions
            "maybe a real",  # Meta-suggestions
            "maybe compare",  # Planning text
            "maybe discuss",  # Planning text
            "maybe include",  # Planning text
            "maybe mention",  # Planning text
            "paragraph:",  # Structural/outline markers
            "first paragraph",
            "second paragraph",
            "third paragraph",
            "fourth paragraph",
            "fifth paragraph",
            "first:",  # Structural numbered lists
            "second:",
            "third:",
            "fourth:",
            "fifth:",
            "sixth:",
            # Planning/outline content
            "need to explain",
            "need to make",
            "need to ensure",
            "also, avoid",
            "also, no",
            "also, check",
            "also,-----",  # Truncated content
            "avoid jargon",
            "avoid using",  # Format instructions
            "avoid meta",
            "use analogies",
            "use a analogy",
            "use intuitive",
            "use examples like",  # Meta-instructions
            "use clear",  # Meta-instructions
            "use a comparison",  # Meta-instructions
            "check if ",
            "check if there",
            "start directly",
            "don't say",
            "don't forget",
            "try to avoid",
            "ensure each",
            "maybe not",  # Uncertain suggestions
            "so no",  # Planning statements
            "then, i need",  # Sequential planning
            "keep it flowing",  # Format instructions
            "no bullet",  # Format instructions
            "no 'i'll",  # Meta-instructions
            "four to five",  # Paragraph count instructions
            "make it engaging",  # Tone instructions
            "that structure",  # Planning evaluation
            "that analogy",  # Planning evaluation
            "just dive",  # Instructions on how to write
            "key point for",  # Emphasis markers in planning
            "also, make",  # Additional planning
            "also, mention",  # Planning content
            "should work",  # Planning evaluation
            "can affect",  # Sometimes thinking but watch for "pollution can affect"
            "that's a key",  # Retrospective evaluation
            "that's part of the",  # Meta-commentary
            "that's the ",  # Identification statements in planning context
            "then, when",  # Sequential storytelling that's planning
            "the basic flow",  # Structural description
            # Level-based planning content
            "use examples they",  # Planning instruction
            "avoid technical",  # Planning instruction
            "or a journey",  # Planning suggestion
            "then tie it",  # Planning instruction
            "use active",  # Planning instruction
            "emphasize that",  # Meta-instruction (often in planning)
            "comparing",  # Often indicates thinking/structuring
            "that might help",  # Planning rationale
            "1. ", "2. ", "3. ", "4. ", "5. ",  # Numbered outline markers
            "2. evaporation",  # Numbered list markers
            "3. condensation",
            "4. precipitation",
            "let them visualize",  # Meta-instruction
            "help them visualize",  # Meta-instruction
            "tie it all together",  # Planning language
            "importance and",  # Section title from planning
            "conclusion",  # Planning structure
            "or a story",  # Alternative structuring
            "so i shouldn",  # First person meta-thinking
            # Explicit meta-reasoning phrases
            "that could work",  # Planning evaluation
            "would be good",  # Planning evaluation
            "putting it all together",  # Planning meta-commentary
            "need to mention",  # Planning content
            "use words like",  # Planning instruction
            "use a toy",  # Planning instruction
            "use a story",  # Planning instruction
            "use sentences",  # Planning instruction
            "make sure the",  # Planning instruction
            "check for clarity",  # Planning instruction
            "no technical",  # Planning instruction
            "okay, putting",  # Planning transition
            "use simpler terms",  # Planning instruction
        ]
        
        for pattern in meta_patterns:
            if pattern in s:
                return True
        
        # Filter out obviously incomplete thoughts
        if sentence.endswith(",") and len(sentence) < 30:
            return True
        
        # Filter out single-phrase hedges with question marks at end (uncertainty)
        if "?" in s and len(sentence.split()) < 5:
            return True
        
        return False
    
    async def find_past_struggles(self, topic: str, confusion_level: int, days: int = 30, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Main method: Find similar confusion moments + what helped, with LLM-generated recommendation and adaptive explanation.
        
        CRITICAL: Automatically retains this interaction to hindsight for future recalls.
        """
        # Call core service to find historical struggles
        result = await self.hindsight.recall_temporal_archaeology(
            topic=topic,
            confusion_level=confusion_level,
            days=days,
            user_id=user_id,
        )

        insights = await self.hindsight.get_user_insights(user_id)
        memory_context = self._format_insights(insights)
        
        # Use LLM to enhance recommendation only if we have helpful hints to base it on
        what_helped = result.get("what_helped_before", [])
        if what_helped and any(h.get("hint_used") for h in what_helped):
            hints_summary = "\n".join([f"- {h.get('hint_used', 'unknown')}" for h in what_helped[:3] if h.get("hint_used")])
            if hints_summary:
                prompt = f"""User history:
{memory_context}

Current question:
How to improve understanding of {topic} based on what helped before.

Instruction:
Adapt explanation based on user's past struggles.

Based on what helped before for {topic}:

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
        
        # Generate adaptive explanation based on confusion level
        try:
            explanation_prompt, audience_type = self._build_explanation_prompt(topic, confusion_level)
            explanation_prompt = f"""User history:
{memory_context}

Current question:
Explain {topic} at confusion level {confusion_level}.

Instruction:
Adapt explanation based on user's past struggles.

{explanation_prompt}"""
            explanation_raw = self.llm.generate(explanation_prompt, max_tokens=1200, temperature=0.5)
            # Clean the explanation using same logic as recommendation
            explanation = self._clean_explanation_text(explanation_raw)
            
            # Only add if we got meaningful content
            if explanation and len(explanation) > 50:
                result["adaptive_explanation"] = explanation
                result["explanation_audience"] = audience_type
        except Exception as e:
            # Fallback: provide a simple guidance if LLM fails
            result["adaptive_explanation"] = f"Review the concept of {topic} step-by-step and focus on building intuition through examples."
            result["explanation_audience"] = "fallback"
        
        # Add feature-specific analysis with single confidence based on confusion_level
        from uuid import uuid4
        response_id = str(uuid4())
        final_result = {
            "response_id": response_id,
            "feature": "temporal_archaeology",
            "query": {"topic": topic, "confusion_level": confusion_level},
            "confidence": self._calculate_confidence_from_confusion(confusion_level),
            "result": result,
            "actionable": len(what_helped) > 0
        }
        
        # ⚡ CRITICAL: Retain this interaction to hindsight for future recalls
        suggested_strategy = "visual_analogy"
        if what_helped and isinstance(what_helped, list):
            first_hint = what_helped[0].get("hint_used") if isinstance(what_helped[0], dict) else None
            if first_hint:
                suggested_strategy = str(first_hint)

        await self._retain_interaction(
            content=(
                f"Student hit confusion again about {topic}. "
                f"Previous strategy [{suggested_strategy}] suggested."
            ),
            user_id=user_id,
            topic=topic,
            engine_feature="archaeology",
            interaction_data={
                "confusion_level": confusion_level,
                "confidence": final_result["confidence"],
                "similar_moments": result.get("similar_moments", 0),
                "suggested_strategy": suggested_strategy,
            }
        )
        
        return final_result
    
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