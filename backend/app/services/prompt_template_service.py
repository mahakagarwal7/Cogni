"""
🎯 PHASE 9: Killer Prompt Design
Adaptive tutor system that learns from memory and adjusts explanation style.

Core template:
- Build memory context from user insights and history
- Apply adaptive rules based on struggles, confidence, and patterns
- Inject into all generation to personalize responses
"""
from typing import Optional, List, Dict, Any
from app.services.hindsight_service import hindsight_service


class PromptTemplateService:
    """
    Killer Prompt: Adaptive tutor prompt generator using memory context.
    """

    def __init__(self):
        self.base_instruction = """You are an adaptive AI tutor for metacognitive learning.

Your primary goal: Help the student learn by adapting to their unique struggles and learning patterns.

CRITICAL ADAPTIVE RULES:
1. If user struggled before with similar concepts → SIMPLIFY the explanation and break into smaller steps
2. If user has LOW CONFIDENCE on this topic → PROVIDE CONCRETE EXAMPLES with step-by-step walkthroughs
3. If user has REPEATED MISTAKES on this pattern → CHANGE EXPLANATION STYLE (use analogies, diagrams, visual language instead)
4. If user PREFERS CERTAIN STYLE → HONOR that preference in tone, depth, and format

ADAPTIVE EXPLANATION STYLES:
- step-by-step: Break down complex ideas into numbered steps
- example-driven: Lead with real examples before theory
- guided: Use Socratic questioning to guide discovery
- concise: Short, direct explanations with minimal extra detail
- visual: Use spatial/connection language, metaphors, structural comparisons

BEFORE ANSWERING:
- Check the user's history: What topics caused confusion? What explanation style worked before?
- Detect patterns: Are there recurring misconceptions or struggles?
- Measure confidence: Is the user uncertain? Provide more scaffolding.
- Honor preferences: Use the student's preferred explanation style.

NOW RESPOND TO THE STUDENT'S QUERY WITH FULL PERSONALIZATION:"""

    async def build_memory_context(
        self, user_id: str, query: str, current_topic: Optional[str] = None
    ) -> str:
        """
        Build rich memory context from user's learning history and insights.
        Returns formatted context to inject into prompt.
        
        Key insight: Even new users should get SOME adaptive context.
        Filter intelligently: only skip records that are DOUBLY generic (issue=none AND topic=general).
        """
        try:
            # Fetch user insights from Hindsight memory
            insights = await hindsight_service.get_user_insights(user_id)
            
            if not insights:
                return "This is a new student. Provide clear, foundational explanations. Use concrete examples."
            
            # Extract key patterns from insights - use PARTIAL matches too
            weak_topics: List[str] = []
            low_confidence_topics: List[str] = []
            repeated_mistakes: List[str] = []
            preferred_styles: List[str] = []
            all_confidence_scores: List[float] = []
            
            real_issues_found = False
            
            for insight in insights:
                if not isinstance(insight, dict):
                    continue
                    
                data = insight.get("data") or {}
                issue = str(data.get("issue", "")).strip().lower()
                topic = str(data.get("topic", "")).strip().lower()
                raw_topic = str(data.get("topic", "")).strip()
                raw_issue = str(data.get("issue", "")).strip()
                
                # Track if we have ANY real issue signal (not bootstrap)
                if issue not in {"", "none"} or topic not in {"", "general", "unknown"}:
                    real_issues_found = True
                
                # Collect confidence for trend analysis
                confidence = data.get("confidence_score", 0)
                if isinstance(confidence, (int, float)):
                    all_confidence_scores.append(float(confidence))
                
                # Skip DOUBLY generic records (both issue and topic trivial)
                if issue in {"", "none"} and topic in {"", "general", "unknown"}:
                    continue
                
                # Collect weak topics (even if topic is generic but issue is real)
                if raw_topic and raw_topic.lower() not in {"general", "unknown"} and issue not in {"", "none", "resolved", "mastered"}:
                    weak_topics.append(raw_topic)
                
                # Collect low confidence areas
                if isinstance(confidence, (int, float)) and confidence < 0.65:
                    if raw_topic and raw_topic.lower() not in {"general", "unknown"}:
                        low_confidence_topics.append(raw_topic)
                
                # Collect repeated issue patterns (even generic ones if repeated)
                if raw_issue and raw_issue.lower() not in {"", "none", "resolved", "mastered"}:
                    repeated_mistakes.append(raw_issue)
                
                # Collect preferred explanation styles
                style = str(data.get("preferred_style", "")).strip()
                if style and style.lower() not in {"guided", "default", "adaptive"}:
                    preferred_styles.append(style)
            
            # Build context string
            context_parts = ["User Profile:"]
            
            # Even if no specific weak topics, mention confidence trend
            if all_confidence_scores:
                avg_conf = sum(all_confidence_scores) / len(all_confidence_scores)
                if avg_conf < 0.65:
                    context_parts.append(f"- Student showing LOW CONFIDENCE ({avg_conf:.2f}) → PROVIDE EXTRA SCAFFOLDING AND EXAMPLES")
                elif avg_conf >= 0.8:
                    context_parts.append(f"- Student showing HIGH CONFIDENCE ({avg_conf:.2f}) → CAN HANDLE CHALLENGING PROBLEMS")
            
            if weak_topics:
                unique_weak = list(set(weak_topics))[:5]
                context_parts.append(f"- Has struggled with: {', '.join(unique_weak)} → EXPLAIN THOROUGHLY")
            
            if low_confidence_topics:
                unique_low_conf = list(set(low_confidence_topics))[:3]
                context_parts.append(
                    f"- Low confidence areas: {', '.join(unique_low_conf)} "
                    f"→ PROVIDE DETAILED EXAMPLES AND STEP-BY-STEP BREAKDOWN"
                )
            
            if repeated_mistakes:
                unique_mistakes = list(set(repeated_mistakes))[:4]
                context_parts.append(
                    f"- Repeated mistakes: {', '.join(unique_mistakes)} "
                    f"→ CHANGE APPROACH, USE ANALOGIES OR VISUAL LANGUAGE"
                )
            
            if preferred_styles:
                style_counts = {}
                for s in preferred_styles:
                    style_counts[s] = style_counts.get(s, 0) + 1
                most_common_style = max(style_counts, key=style_counts.get)
                context_parts.append(
                    f"- Prefers: {most_common_style} explanations → USE THIS STYLE"
                )

            # For truly new users with no insights, use adaptive baseline
            if not real_issues_found:
                context_parts = [
                    "This is a new student with no history yet.",
                    "- Start with CLEAR, FOUNDATIONAL explanations",
                    "- Use CONCRETE EXAMPLES before abstract theory",
                    "- Check for understanding frequently",
                    "- Be prepared to SIMPLIFY or provide ANALOGIES"
                ]
            
            # Mention current topic if relevant
            if current_topic and current_topic.lower() in [t.lower() for t in weak_topics]:
                context_parts.append(
                    f"\n⚠️  ALERT: Student struggled before with '{current_topic}' "
                    f"→ USE EXTRA CARE, SIMPLER LANGUAGE, MORE EXAMPLES"
                )
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[WARNING] Failed to build memory context: {e}")
            return "Unable to load user history. Provide clear, foundational explanations."

    def build_killer_prompt(
        self, user_id: str, memory_context: str, user_query: str
    ) -> str:
        """
        Build the complete killer prompt with memory context and adaptive rules.
        Ready to pass to LLM.
        """
        prompt = f"""{self.base_instruction}

{memory_context}

STUDENT'S QUERY:
{user_query}

RESPOND NOW, fully personalized to this student's needs:"""
        return prompt

    async def generate_adaptive_prompt(
        self, user_id: str, query: str, topic: Optional[str] = None
    ) -> str:
        """
        End-to-end: Build memory context and generate killer prompt.
        """
        memory_context = await self.build_memory_context(user_id, query, topic)
        killer_prompt = self.build_killer_prompt(user_id, memory_context, query)
        return killer_prompt

    def extract_adaptive_rules_from_context(self, context: str) -> Dict[str, Any]:
        """
        Parse memory context to extract actionable adaptive rules for engines.
        Returns dict of rules to apply when generating responses.
        """
        rules = {
            "simplify": False,
            "provide_examples": False,
            "change_style": False,
            "preferred_style": "guided",
        }
        
        if "Low confidence" in context or "low confidence" in context:
            rules["provide_examples"] = True
        
        if "struggled before" in context or "STRUGGLED" in context:
            rules["simplify"] = True
        
        if "Repeated mistakes" in context or "CHANGE EXPLANATION" in context:
            rules["change_style"] = True
        
        if "Prefers:" in context:
            # Extract style from context
            lines = context.split("\n")
            for line in lines:
                if "Prefers:" in line:
                    # Try to extract style name
                    if "step-by-step" in line:
                        rules["preferred_style"] = "step-by-step"
                    elif "example" in line.lower():
                        rules["preferred_style"] = "example-driven"
                    elif "concise" in line.lower():
                        rules["preferred_style"] = "concise"
                    elif "visual" in line.lower():
                        rules["preferred_style"] = "visual"
        
        return rules


# Singleton instance
prompt_template_service = PromptTemplateService()
