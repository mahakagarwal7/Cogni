# backend/app/engines/contagion_engine.py
"""
🌐 Feature 5: Metacognitive Contagion
Learn from anonymized patterns of similar thinkers.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from typing import Dict, Any, List
import json

class ContagionEngine:
    """
    Metacognitive Contagion Engine - Collective intelligence from peer patterns.
    Intelligent hybrid approach: Hindsight memory + LLM reasoning.
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
    
    async def get_community_insights(self, error_pattern: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Get insights personalized to THIS student's learning history.
        HINDSIGHT-FIRST PRIORITY CHAIN (Deterministic, not random):
        
        1. Extract strategies from Hindsight-backed personal study history (deterministic)
        2. Query peer patterns from Hindsight community data (deterministic)
        3. Use LLM only for personalization refinement (when memory exists)
        4. Fall back to curated strategies (always available)
        
        This ensures responses are grounded in real memory, not random LLM generation.
        """
        topic = error_pattern
        
        insights = await self.hindsight.get_user_insights(user_id)
        memory_context = self._format_insights(insights)
        
        # PRIORITY 1: Extract strategies from THIS STUDENT'S actual learning history
        student_memories = await self.hindsight.recall_all_memories(limit=20)
        personal_context = await self._extract_personal_patterns(
            student_memories=student_memories,
            error_pattern=topic
        )
        
        # Deterministic extraction of personal strategies (no LLM randomness)
        personal_strategies = self._extract_personal_strategies(personal_context, topic)
        
        # PRIORITY 2: Query Hindsight for peer insights on THIS TOPIC
        hindsight_data = await self.hindsight.recall_global_contagion(topic)
        
        # PRIORITY 3: Merge personal + peer strategies, ranked by relevance
        all_strategies = personal_strategies  # Start with what worked for THIS STUDENT
        if hindsight_data.get("community_size", 0) > 0:
            # Add peer strategies but prioritize personal ones
            all_strategies.extend(self._extract_community_strategies(hindsight_data))
        
        all_strategies = self._deduplicate_strategies(all_strategies)
        
        # PRIORITY 4: Fall back to curated strategies if still empty
        if not all_strategies:
            all_strategies = self._get_demo_strategies(topic)
        
        # PRIORITY 5: Use LLM only for refinement if we have personal history
        refined_result = await self._refine_for_student(
            error_pattern=topic,
            strategies=all_strategies,
            personal_context=personal_context,
            memory_context=memory_context
        )
        
        # Generate learning plan (uses Hindsight + personal context)
        peer_strategies = hindsight_data.get("top_strategy", "")
        learning_plan = await self._generate_learning_plan(
            topic=topic,
            peer_strategies=peer_strategies,
            personal_context=personal_context,
            memory_context=memory_context,
            personal_strategies=personal_strategies
        )
        
        # Build response (backward compatible + improvements)
        from uuid import uuid4
        response_id = str(uuid4())
        result = {
            "response_id": response_id,
            "feature": "metacognitive_contagion",
            "error_pattern": error_pattern,
            "community_size": hindsight_data.get("community_size", 0),
            "top_strategy": refined_result.get("top_strategy", self._generate_default_strategy(topic)),
            "success_rate": refined_result.get("success_rate", 0.79),
            "privacy_note": "Personalized based on your learning history + peer patterns",
            "additional_strategies": refined_result.get("strategies", []),
            "learning_plan": learning_plan,
            "demo_mode": hindsight_data.get("demo_mode", True),
            "grounded_in_memory": len(personal_strategies) > 0  # NEW: Show if grounded in real memory
        }
        
        # ⚡ CRITICAL: Retain this interaction to hindsight for future recalls
        await self._retain_interaction(
            content=f"Contagion query for {topic}: {len(personal_strategies)} personal strategies + {len(all_strategies)} total strategies",
            user_id=user_id,
            topic=topic,
            engine_feature="contagion",
            interaction_data={
                "community_size": result["community_size"],
                "personal_strategies_count": len(personal_strategies),
                "success_rate": result["success_rate"],
                "strategy": str(result.get("top_strategy", ""))[:100]
            }
        )
        
        return result
    
    async def _extract_personal_patterns(
        self,
        student_memories: List[Dict[str, Any]],
        error_pattern: str
    ) -> Dict[str, Any]:
        """
        Extract patterns from student's personal learning history.
        Identify what strategies have worked for them before.
        """
        if not student_memories:
            return {
                "successful_strategies": [],
                "past_struggles": [],
                "learning_style": "unknown",
                "confidence": 0.5
            }
        
        # Analyze memory contents for successful patterns
        successful_strategies = []
        past_struggles = []
        
        for memory in student_memories:
            content = memory.get("content", "").lower()
            
            # Look for success indicators
            if any(word in content for word in ["worked", "success", "understood", "mastered", "solved"]):
                if "strategy" in content or "approach" in content or "practice" in content:
                    successful_strategies.append(memory.get("content", ""))
            
            # Look for struggle indicators
            if any(word in content for word in ["struggled", "confused", "difficulty", "hard", "error"]):
                past_struggles.append(memory.get("content", ""))
        
        # Use LLM to infer learning style from patterns
        learning_style = await self._infer_learning_style(student_memories)
        
        return {
            "successful_strategies": successful_strategies[:5],
            "past_struggles": past_struggles[:3],
            "learning_style": learning_style,
            "confidence": min(0.95, 0.5 + (len(student_memories) * 0.05))  # More memories = higher confidence
        }
    
    def _extract_personal_strategies(self, personal_context: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
        """
        DETERMINISTIC extraction of strategies from student's successful history.
        No LLM randomness - grounded in real memory.
        """
        strategies = []
        
        # Extract successful strategies from memory
        for successful in personal_context.get("successful_strategies", []):
            if successful:
                strategies.append({
                    "strategy": successful[:120],
                    "success_rate": 0.85,
                    "source": "from_your_learning_history"
                })
        
        # Map past struggles to recommended strategies
        for struggle in personal_context.get("past_struggles", [])[:2]:
            if struggle:
                # Generate practical strategy for this struggle
                counter_strategy = self._generate_counter_strategy(struggle, topic)
                if counter_strategy:
                    strategies.append({
                        "strategy": counter_strategy,
                        "success_rate": 0.82,
                        "source": "addressing_your_past_struggles"
                    })
        
        return strategies
    
    def _generate_counter_strategy(self, struggle: str, topic: str) -> str:
        """
        Generate a practical counter-strategy for a specific struggle.
        Deterministic - not random.
        """
        struggle_lower = struggle.lower()
        
        # Map struggles to counter-strategies
        if any(word in struggle_lower for word in ["confused", "unclear", "understand"]):
            return f"Work through detailed tutorials or visualizations specific to {topic}"
        elif any(word in struggle_lower for word in ["hard", "difficulty", "can't"]):
            return f"Start with simpler variants of {topic} and gradually increase complexity"
        elif any(word in struggle_lower for word in ["error", "wrong", "failed", "mistake"]):
            return f"Trace through working examples step-by-step to identify your error patterns"
        elif any(word in struggle_lower for word in ["forget", "remember", "retention"]):
            return f"Practice {topic} regularly with spaced repetition and varied problems"
        else:
            return f"Practice {topic} with focused exercises and track your improvements"
    
    def _extract_community_strategies(self, hindsight_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract strategies from community/peer data.
        """
        strategies = []
        
        if hindsight_data.get("top_strategy"):
            strategies.append({
                "strategy": f"Peer success: {hindsight_data.get('top_strategy')}",
                "success_rate": hindsight_data.get("success_rate", 0.79),
                "source": "from_peer_community"
            })
        
        # Add additional community strategies
        for strat in hindsight_data.get("additional_strategies", [])[:3]:
            if isinstance(strat, dict) and strat.get("strategy"):
                strategies.append({
                    "strategy": strat.get("strategy"),
                    "success_rate": strat.get("success_rate", 0.75),
                    "source": "from_peer_community"
                })
        
        return strategies
    
    def _deduplicate_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate strategies and sort by success rate.
        """
        seen = set()
        unique = []
        
        for s in strategies:
            text = s.get("strategy", "").lower()[:50]
            if text not in seen:
                seen.add(text)
                unique.append(s)
        
        # Sort by success rate (descending)
        unique.sort(key=lambda s: s.get("success_rate", 0.5), reverse=True)
        
        return unique[:5]
    
    async def _generate_topic_strategies(
        self,
        topic: str,
        personal_context: Dict[str, Any],
        hindsight_data: Dict[str, Any],
        memory_context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate strategies dynamically for ANY topic using LLM + Hindsight.
        This replaces hardcoded strategy maps with intelligent, topic-specific generation.
        """
        strategies = []
        
        # Priority 1: Strategies from student's successful history
        for successful in personal_context.get("successful_strategies", []):
            if successful:
                strategies.append({
                    "strategy": successful[:100],
                    "success_rate": 0.85,
                    "source": "from_your_history"
                })
        
        # Priority 2: Use LLM to generate topic-specific strategies
        if self.llm.available:
            learning_style = personal_context.get("learning_style", "adaptive")
            
            prompt = f"""User history:
{memory_context}

Current question:
Generate actionable strategies for mastering {topic}.

Instruction:
Adapt explanation based on user's past struggles.

Generate 4 SPECIFIC, ACTIONABLE strategies for learning/mastering "{topic}".

Tailor to "{learning_style}" learning style.
Focus on: practical exercises, visualization, peer learning approaches.

CRITICAL FORMAT - respond EXACTLY like this with NO preamble:

Strategy: [Specific action for learning {topic}]
Success: [0.75-0.95]

Strategy: [Specific action for learning {topic}]
Success: [0.75-0.95]

Strategy: [Specific action for learning {topic}]
Success: [0.75-0.95]

Strategy: [Specific action for learning {topic}]
Success: [0.75-0.95]"""

            try:
                response = self.llm.generate(prompt, max_tokens=300, temperature=0.5)
                response = response.replace("<think>", "").replace("</think>", "").strip()
                
                lines = response.split('\n')
                current_strategy = None
                for line in lines:
                    cleaned_line = line.replace("**", "").strip()
                    if cleaned_line.startswith("Strategy:"):
                        current_strategy = cleaned_line.replace("Strategy:", "").strip()
                    elif cleaned_line.startswith("Success:") and current_strategy:
                        try:
                            success_rate = float(cleaned_line.replace("Success:", "").strip())
                            strategies.append({
                                "strategy": current_strategy,
                                "success_rate": min(0.95, max(0.50, success_rate)),
                                "source": "generated_for_topic"
                            })
                            current_strategy = None
                        except ValueError:
                            pass
                
                if strategies:  # If LLM generated strategies, we're good
                    return strategies[:5]
                    
            except Exception as e:
                print(f"[DEBUG] LLM strategy generation for '{topic}' failed: {e}")
        
        # Priority 3: Fall back to Hindsight community data
        if hindsight_data.get("community_size", 0) > 0:
            community_strategy = hindsight_data.get("top_strategy", "")
            if community_strategy:
                strategies.append({
                    "strategy": f"Peer success: {community_strategy}",
                    "success_rate": hindsight_data.get("success_rate", 0.79),
                    "source": "from_community"
                })
        
        # Priority 4: Baseline strategies (used when no personalized/peer strategy was generated)
        fallback = [
            {
                "strategy": f"Start with fundamental concepts in {topic}",
                "success_rate": 0.80,
                "source": "baseline"
            },
            {
                "strategy": f"Practice problems related to {topic} progressively",
                "success_rate": 0.82,
                "source": "baseline"
            },
            {
                "strategy": f"Study peer solutions and approaches to {topic}",
                "success_rate": 0.78,
                "source": "baseline"
            },
            {
                "strategy": f"Build a project or apply {topic} in real scenarios",
                "success_rate": 0.85,
                "source": "baseline"
            }
        ]
        strategies.extend(fallback)
        
        # Deduplicate
        seen = set()
        unique = []
        for s in strategies:
            text = s.get("strategy", "").lower()[:40]
            if text not in seen:
                seen.add(text)
                unique.append(s)
        
        return unique[:5]
    
    async def _generate_learning_plan(
        self,
        topic: str,
        peer_strategies: str,
        personal_context: Dict[str, Any],
        memory_context: str = "",
        personal_strategies: List[Dict[str, Any]] | None = None,
    ) -> str:
        """
        UPGRADE: Generate a mentor-guided learning plan for the topic using LLM.
        
        Returns a clean, readable roadmap with 4-6 steps.
        Each step explains WHAT to do and WHY.
        No percentages, bullet symbols, or meta explanations.
        """
        if not self.llm.available:
            return self._build_fallback_learning_plan(
                topic=topic,
                personal_context=personal_context,
                peer_strategies=peer_strategies,
                personal_strategies=personal_strategies,
            )
        
        # Build context
        learning_style = personal_context.get("learning_style", "adaptive")
        peer_benefit = f" What helped others: {peer_strategies}." if peer_strategies else ""
        
        prompt = f"""User history:
    {memory_context}

    Current question:
    Create a learning roadmap for {topic}.

    Instruction:
    Adapt explanation based on user's past struggles.

    You are a mentor creating a personalized learning roadmap.

Topic: {topic}
Student's learning style: {learning_style}
{peer_benefit}

Create a structured learning plan for {topic}.

CRITICAL REQUIREMENTS:
- 4 to 6 clear steps
- Each step explains WHAT to do and WHY it matters
- Write as readable paragraphs, NOT bullet lists
- NO percentage signs or numbers like "70%"
- NO meta explanations like "let me explain" or "here's why"
- NO thinking steps or brackets like <think>
- NO truncation - complete thoughts only
- Mentor-like, encouraging, practical tone
- Focus on understanding and mastery

Format: Just the plan text, nothing else."""

        try:
            response = self.llm.generate(prompt, max_tokens=800, temperature=0.6)
            
            # Clean output: remove thinking tags
            cleaned = response.replace("<think>", "").replace("</think>", "").strip()
            
            # Remove meta-explanation lines
            meta_patterns = [
                "let me",
                "here's",
                "the key is",
                "you should know",
                "first of all",
                "to be clear",
                "in short"
            ]
            
            lines = cleaned.split("\n")
            cleaned_lines = []
            skip_next = False
            
            for line in lines:
                lower_line = line.lower().strip()
                
                # Skip intro/meta lines
                is_meta = any(meta in lower_line for meta in meta_patterns)
                
                if is_meta and len(line) < 50:
                    skip_next = True
                    continue
                
                if skip_next and len(line.strip()) == 0:
                    skip_next = False
                    continue
                
                skip_next = False
                
                # Remove asterisks (markdown bold)
                clean_line = line.replace("**", "").replace("*", "")
                
                if clean_line.strip():
                    cleaned_lines.append(clean_line)
            
            final_plan = "\n\n".join(cleaned_lines).strip()
            
            # Fallback if empty
            if not final_plan or len(final_plan) < 120:
                return self._build_fallback_learning_plan(
                    topic=topic,
                    personal_context=personal_context,
                    peer_strategies=peer_strategies,
                    personal_strategies=personal_strategies,
                )
            
            return final_plan
            
        except Exception as e:
            print(f"[DEBUG] Learning plan generation failed: {e}")
            return self._build_fallback_learning_plan(
                topic=topic,
                personal_context=personal_context,
                peer_strategies=peer_strategies,
                personal_strategies=personal_strategies,
            )

    def _build_fallback_learning_plan(
        self,
        topic: str,
        personal_context: Dict[str, Any],
        peer_strategies: str,
        personal_strategies: List[Dict[str, Any]] | None = None,
    ) -> str:
        """Deterministic full roadmap fallback when LLM output is unavailable/weak."""
        learning_style = str(personal_context.get("learning_style", "adaptive"))
        strategy_rows = personal_strategies or []
        top_personal = ""
        for row in strategy_rows:
            strategy_text = str(row.get("strategy", "")).strip()
            if strategy_text:
                top_personal = strategy_text
                break

        peer_hint = str(peer_strategies or "").strip()
        style_nudge = {
            "visual": "Use diagrams, maps, and visual traces while studying each step.",
            "kinesthetic": "Write and run small examples in each step before moving on.",
            "auditory": "Explain each step out loud to check if your reasoning is clear.",
            "reading-writing": "Summarize each step in your own words after solving one example.",
            "adaptive": "Switch between examples, short notes, and quick practice checks.",
        }.get(learning_style, "Switch between examples, short notes, and quick practice checks.")

        step_two = (
            f"Step 2: Practice one focused method that has worked in your history: {top_personal}. "
            "Run it on 3 small examples and write why each attempt worked or failed."
            if top_personal
            else f"Step 2: Solve 3 small, focused exercises on {topic} and capture the exact mistake pattern in each attempt."
        )

        step_three = (
            f"Step 3: Add a peer-proven approach: {peer_hint}. "
            "Compare it against your current approach and keep the parts that reduce mistakes fastest."
            if peer_hint
            else f"Step 3: Review one high-quality peer solution for {topic} and compare its decision process with your own."
        )

        return (
            f"Step 1: Start by breaking {topic} into 3 core subskills and study them in order from easiest to hardest. "
            "For each subskill, define one success checkpoint so progress is measurable.\n\n"
            f"{step_two}\n\n"
            f"{step_three}\n\n"
            f"Step 4: Build one integrated practice task on {topic} that combines all subskills. "
            "After finishing, reflect on where confusion returned and revise your checklist before the next session.\n\n"
            f"Step 5: Use this learning-style guide every session: {style_nudge}"
        )
    
    def _generate_default_strategy(self, topic: str) -> str:
        """Generate a sensible default strategy for any topic."""
        return f"Break down {topic} into smaller, manageable components and practice systematically"
    
    async def _infer_learning_style(self, student_memories: List[Dict[str, Any]]) -> str:
        """
        Use LLM to infer student's learning style from memory patterns.
        """
        if not self.llm.available or not student_memories:
            return "adaptive"
        
        # Summarize memories for LLM
        memory_summary = "\n".join([
            m.get("content", "")[:100] for m in student_memories[:5]
        ])
        
        prompt = f"""Based on this student's learning history, infer ONE learning style:

{memory_summary}

Choose ONE: visual, kinesthetic, auditory, reading-writing, adaptive

Respond with ONLY the style name, nothing else."""

        try:
            response = self.llm.generate(prompt, max_tokens=10, temperature=0.2)
            style = response.strip().lower()
            if style in ["visual", "kinesthetic", "auditory", "reading-writing", "adaptive"]:
                return style
        except:
            pass
        
        return "adaptive"
    
    async def _get_personalized_strategies(
        self,
        error_pattern: str,
        personal_context: Dict[str, Any],
        community_size: int
    ) -> List[Dict[str, Any]]:
        """
        Generate strategies prioritized by student's successful history.
        Use what has worked for THEM before as primary source.
        """
        strategies = []
        
        # Priority 1: Strategies from student's successful history
        for successful in personal_context.get("successful_strategies", []):
            if successful:
                strategies.append({
                    "strategy": successful[:100],
                    "success_rate": 0.85,
                    "source": "from_your_history"
                })
        
        # Priority 2: Generate new strategies based on learning style
        learning_style = personal_context.get("learning_style", "adaptive")
        
        llm_strategies = []
        if self.llm.available:
            prompt = f"""Generate 3 specific, actionable learning strategies for a student struggling with "{error_pattern}".
Tailor the strategies to a "{learning_style}" learning style. Make them highly specific to the exact topic.

CRITICAL: Respond EXACTLY in this text format. NO preamble, NO markdown, NO thinking.

Strategy: [Specific, actionable step]
Success: [0.70-0.95]

Strategy: [Specific, actionable step]
Success: [0.70-0.95]

Strategy: [Specific, actionable step]
Success: [0.70-0.95]"""

            try:
                response = self.llm.generate(prompt, max_tokens=250, temperature=0.4)
                response = response.replace("<think>", "").replace("</think>", "").strip()
                
                lines = response.split('\n')
                current_strategy = None
                for line in lines:
                    cleaned_line = line.replace("**", "").strip()
                    if cleaned_line.startswith("Strategy:"):
                        current_strategy = cleaned_line.replace("Strategy:", "").strip()
                    elif cleaned_line.startswith("Success:") and current_strategy:
                        try:
                            success_rate = float(cleaned_line.replace("Success:", "").strip())
                            llm_strategies.append({
                                "strategy": current_strategy,
                                "success_rate": min(0.95, max(0.50, success_rate)),
                                "source": "learning_style"
                            })
                            current_strategy = None
                        except ValueError:
                            pass
            except Exception as e:
                print(f"[DEBUG] Topic-specific strategy generation failed: {e}")
        
        if llm_strategies:
            strategies.extend(llm_strategies)
        else:
            style_strategies = self._get_strategies_for_style(learning_style, error_pattern)
            strategies.extend(style_strategies)
        
        # Priority 3: Community backup strategies
        if community_size > 0:
            strategies.append({
                "strategy": f"Review standard peer solutions for {error_pattern}",
                "success_rate": 0.79,
                "source": "from_community"
            })
        
        # Ensure diversity and deduplicate
        seen = set()
        unique = []
        for s in strategies:
            text = s.get("strategy", "").lower()[:30]
            if text not in seen:
                seen.add(text)
                unique.append(s)
        
        return unique[:5]
    
    def _get_strategies_for_style(self, learning_style: str, error_pattern: str) -> List[Dict[str, Any]]:
        """
        Get strategies tailored to student's learning style.
        """
        style_map = {
            "visual": [
                {"strategy": "Draw diagrams and visualize the problem", "success_rate": 0.88, "source": "learning_style"},
                {"strategy": "Use flowcharts to trace execution", "success_rate": 0.85, "source": "learning_style"},
                {"strategy": "Watch algorithm animations", "success_rate": 0.82, "source": "learning_style"}
            ],
            "kinesthetic": [
                {"strategy": "Practice with hands-on coding", "success_rate": 0.87, "source": "learning_style"},
                {"strategy": "Type out examples to build muscle memory", "success_rate": 0.86, "source": "learning_style"},
                {"strategy": "Build projects to apply concepts", "success_rate": 0.84, "source": "learning_style"}
            ],
            "auditory": [
                {"strategy": "Explain the problem out loud", "success_rate": 0.84, "source": "learning_style"},
                {"strategy": "Discuss with peers or rubber duck", "success_rate": 0.81, "source": "learning_style"},
                {"strategy": "Listen to code walkthroughs", "success_rate": 0.79, "source": "learning_style"}
            ],
            "reading-writing": [
                {"strategy": "Read detailed documentation", "success_rate": 0.85, "source": "learning_style"},
                {"strategy": "Write out step-by-step solutions", "success_rate": 0.86, "source": "learning_style"},
                {"strategy": "Study written examples", "success_rate": 0.83, "source": "learning_style"}
            ],
            "adaptive": [
                {"strategy": "Practice with smaller test cases", "success_rate": 0.79, "source": "learning_style"},
                {"strategy": "Break problem into smaller steps", "success_rate": 0.75, "source": "learning_style"},
                {"strategy": "Review similar solved examples", "success_rate": 0.73, "source": "learning_style"}
            ]
        }
        
        return style_map.get(learning_style, style_map["adaptive"])
    
    async def _refine_for_student(
        self,
        error_pattern: str,
        strategies: List[Dict[str, Any]],
        personal_context: Dict[str, Any],
        memory_context: str = ""
    ) -> Dict[str, Any]:
        """
        Use LLM to personalize strategy recommendations based on student's history.
        """
        if not strategies:
            return {
                "top_strategy": f"Break down {error_pattern} into smaller components",
                "success_rate": 0.79,
                "strategies": []
            }
        
        # Check if we have personal history to leverage
        has_history = len(personal_context.get("successful_strategies", [])) > 0
        learning_style = personal_context.get("learning_style", "adaptive")
        
        if not self.llm.available or not has_history:
            # Use best strategy from list
            return {
                "top_strategy": strategies[0].get("strategy", f"Break down {error_pattern} into smaller components"),
                "success_rate": strategies[0].get("success_rate", 0.79),
                "strategies": strategies
            }
        
        # Use LLM to personalize based on student's history
        prompt = f"""User history:
    {memory_context}

    Current question:
    Rank the best strategy for {error_pattern}.

    Instruction:
    Adapt explanation based on user's past struggles.

    Based on this student's learning history, rank these strategies for: "{error_pattern}"

Their learning style: {learning_style}
Strategies that worked for them before:
{chr(10).join([f'- {s[:80]}' for s in personal_context.get('successful_strategies', [])[:3]])}

Available strategies:
{chr(10).join([f'- {s.get("strategy", "")}' for s in strategies[:3]])}

Recommend the BEST strategy for THIS STUDENT.
Respond with ONLY:
STRATEGY: [best strategy name]
SUCCESS_RATE: [0.XX]"""

        try:
            response = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
            top_strat = strategies[0].get("strategy", f"Break down {error_pattern} into smaller components")
            success_rate = strategies[0].get("success_rate", 0.79)
            
            lines = response.split("\n")
            for line in lines:
                cleaned_line = line.replace("**", "").strip()
                if cleaned_line.startswith("STRATEGY:"):
                    top_strat = cleaned_line.replace("STRATEGY:", "").strip()
                elif cleaned_line.startswith("SUCCESS_RATE:"):
                    try:
                        success_rate = float(cleaned_line.replace("SUCCESS_RATE:", "").strip())
                    except:
                        pass
            
            return {
                "top_strategy": top_strat,
                "success_rate": min(0.95, max(0.50, success_rate)),
                "strategies": strategies
            }
        except Exception as e:
            print(f"[DEBUG] Student refinement failed: {e}")
        
        return {
            "top_strategy": strategies[0].get("strategy", f"Break down {error_pattern} into smaller components"),
            "success_rate": strategies[0].get("success_rate", 0.79),
            "strategies": strategies
        }
        """
        Use LLM to normalize free-form error descriptions into structured pattern.
        
        Input: "I don't understand recursion base case"
        Output: {"normalized_pattern": "base_case_missing", "topic": "recursion", "error_type": "conceptual_gap"}
        """
        if not self.llm.available:
            # Fallback: extract basic pattern
            return {"topic": "general", "normalized_pattern": error_pattern.lower()}
        
        prompt = f"""Classify this learning problem:

User says: "{error_pattern}"

Extract:
1. Main topic (recursion, arrays, graphs, loops, etc.)
2. Error type (conceptual_gap, implementation_error, edge_case, performance)
3. Normalized pattern (base_case_missing, off_by_one, stack_overflow, etc.)

Respond ONLY with valid JSON:
{{"topic": "...", "error_type": "...", "normalized_pattern": "..."}}"""

        try:
            response = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
            # Remove thinking tags if present
            response = response.replace("<think>", "").replace("</think>", "").strip()
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "topic": parsed.get("topic", "general"),
                    "error_type": parsed.get("error_type", "conceptual_gap"),
                    "normalized_pattern": parsed.get("normalized_pattern", error_pattern.lower())
                }
        except Exception as e:
            print(f"[DEBUG] Pattern normalization failed: {e}")
        
        return {"topic": "general", "normalized_pattern": error_pattern.lower()}
    
    async def _gather_and_rank_strategies(
        self,
        error_pattern: str,
        normalized_info: Dict[str, Any],
        hindsight_data: Dict[str, Any],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Gather strategies from multiple sources and rank by relevance + success.
        
        Sources:
        1. Hindsight community data (if available)
        2. Hardcoded demo strategies (topic-specific)
        3. LLM-generated strategies based on error type
        """
        strategies = []
        
        # Source 1: Hindsight strategies (if community_size > 0)
        if hindsight_data.get("community_size", 0) > 0:
            hindsight_strats = hindsight_data.get("additional_strategies", [])
            strategies.extend(hindsight_strats)
        
        # Source 2: Topic-specific demo strategies
        topic_strategies = self._get_demo_strategies(topic)
        strategies.extend(topic_strategies)
        
        # Source 3: LLM-generated strategies (if LLM available)
        if self.llm.available:
            llm_strategies = await self._generate_strategies_with_llm(
                error_pattern=error_pattern,
                topic=topic,
                error_type=normalized_info.get("error_type", "conceptual_gap")
            )
            strategies.extend(llm_strategies)
        
        # Deduplicate and rank by success_rate
        seen = set()
        unique_strategies = []
        for s in strategies:
            strat_text = s.get("strategy", "").lower()
            if strat_text not in seen:
                seen.add(strat_text)
                unique_strategies.append(s)
        
        # Sort by success_rate (descending)
        unique_strategies.sort(key=lambda s: s.get("success_rate", 0.5), reverse=True)
        
        return unique_strategies[:5]  # Return top 5 unique strategies
    
    async def _generate_strategies_with_llm(
        self,
        error_pattern: str,
        topic: str,
        error_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate context-aware strategies using LLM.
        """
        if not self.llm.available:
            return []
        
        prompt = f"""Generate 2-3 specific learning strategies for this problem:

Topic: {topic}
Problem: {error_pattern}
Error type: {error_type}

For EACH strategy include:
- A specific, actionable step (one sentence)
- Estimated success rate (0.50-0.95)

Respond ONLY with JSON array:
[{{"strategy": "...", "success_rate": 0.XX}}, ...]"""

        try:
            response = self.llm.generate(prompt, max_tokens=200, temperature=0.4)
            response = response.replace("<think>", "").replace("</think>", "").strip()
            
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return [
                    {
                        "strategy": s.get("strategy", ""),
                        "success_rate": min(0.95, max(0.50, float(s.get("success_rate", 0.7))))
                    }
                    for s in parsed if s.get("strategy")
                ]
        except Exception as e:
            print(f"[DEBUG] LLM strategy generation failed: {e}")
        
        return []
    
    async def _refine_top_strategy(
        self,
        error_pattern: str,
        strategies: List[Dict[str, Any]],
        normalized_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to refine top strategy selection and explanation.
        """
        if not strategies or not self.llm.available:
            return {
                "top_strategy": strategies[0].get("strategy", "visual_analogy") if strategies else "visual_analogy",
                "success_rate": strategies[0].get("success_rate", 0.82) if strategies else 0.82,
                "strategies": strategies if strategies else []
            }
        
        # Format strategies for LLM
        strats_text = "\n".join([
            f"- {s.get('strategy')} (success: {s.get('success_rate', 0.7):.0%})"
            for s in strategies[:5]
        ])
        
        prompt = f"""Given these strategies for: "{error_pattern}"

{strats_text}

Rank them by effectiveness for THIS specific problem and explain the top choice.

Respond with ONLY:
TOP_STRATEGY: [strategy text]
SUCCESS_RATE: [0.XX]
EXPLANATION: [1-2 sentences why this is best]"""

        try:
            response = self.llm.generate(prompt, max_tokens=150, temperature=0.3)
            response = response.replace("<think>", "").replace("</think>", "").strip()
            
            lines = response.split("\n")
            top_strat = strategies[0].get("strategy", "visual_analogy")
            success_rate = strategies[0].get("success_rate", 0.82)
            
            for line in lines:
                if line.startswith("TOP_STRATEGY:"):
                    top_strat = line.replace("TOP_STRATEGY:", "").strip()
                elif line.startswith("SUCCESS_RATE:"):
                    try:
                        sr = float(line.replace("SUCCESS_RATE:", "").strip())
                        success_rate = min(0.95, max(0.50, sr))
                    except:
                        pass
            
            return {
                "top_strategy": top_strat,
                "success_rate": success_rate,
                "strategies": strategies
            }
        except Exception as e:
            print(f"[DEBUG] Strategy refinement failed: {e}")
        
        return {
            "top_strategy": strategies[0].get("strategy", "visual_analogy"),
            "success_rate": strategies[0].get("success_rate", 0.82),
            "strategies": strategies
        }
    
    def _get_demo_strategies(self, error_pattern: str) -> List[Dict[str, Any]]:
        """
        Generate realistic demo strategies based on topic/error pattern.
        
        Dynamic fallback for demo/offline mode.
        """
        # Map patterns to topic-specific strategies
        topic_strategies = {
            "recursion": [
                {"strategy": "Write base case first before recursive logic", "success_rate": 0.89},
                {"strategy": "Test with smallest input (n=0 or n=1)", "success_rate": 0.85},
                {"strategy": "Draw the recursion tree visually", "success_rate": 0.82},
                {"strategy": "Trace function calls on paper", "success_rate": 0.84},
                {"strategy": "Check termination condition is reachable", "success_rate": 0.87}
            ],
            "graphs": [
                {"strategy": "Draw the graph structure first", "success_rate": 0.88},
                {"strategy": "Practice BFS and DFS on small examples", "success_rate": 0.85},
                {"strategy": "Implement using adjacency list", "success_rate": 0.80},
                {"strategy": "Mark visited nodes to avoid cycles", "success_rate": 0.89},
                {"strategy": "Use queue or stack for traversal", "success_rate": 0.83}
            ],
            "arrays": [
                {"strategy": "Use pen-and-paper to trace index changes", "success_rate": 0.87},
                {"strategy": "Test boundary conditions (start, end)", "success_rate": 0.88},
                {"strategy": "Verify loop ranges with off-by-one check", "success_rate": 0.86},
                {"strategy": "Use visualization tools for array manipulations", "success_rate": 0.79},
                {"strategy": "Practice with small arrays (n=3, 4)", "success_rate": 0.84}
            ],
            "sorting": [
                {"strategy": "Implement bubble sort first to understand", "success_rate": 0.82},
                {"strategy": "Trace algorithm step-by-step on paper", "success_rate": 0.85},
                {"strategy": "Compare different algorithms (quick, merge, heap)", "success_rate": 0.75},
                {"strategy": "Analyze time complexity (best, avg, worst case)", "success_rate": 0.79},
                {"strategy": "Practice with nearly sorted/reverse arrays", "success_rate": 0.80}
            ],
            "strings": [
                {"strategy": "Master string indexing and slicing", "success_rate": 0.87},
                {"strategy": "Practice character iteration patterns", "success_rate": 0.84},
                {"strategy": "Use regex for pattern matching problems", "success_rate": 0.72},
                {"strategy": "Handle edge cases (empty strings, special chars)", "success_rate": 0.85},
                {"strategy": "Trace through two-pointer approach", "success_rate": 0.83}
            ],
            "dynamic_programming": [
                {"strategy": "Solve brute force version first", "success_rate": 0.88},
                {"strategy": "Build DP table on paper for small inputs", "success_rate": 0.90},
                {"strategy": "Identify overlapping subproblems", "success_rate": 0.81},
                {"strategy": "Practice memoization before tabulation", "success_rate": 0.79},
                {"strategy": "Trace state transitions carefully", "success_rate": 0.87}
            ],
            "loops": [
                {"strategy": "Write loop boundaries on paper first", "success_rate": 0.88},
                {"strategy": "Test edge cases (empty, single element)", "success_rate": 0.84},
                {"strategy": "Check off-by-one errors in conditions", "success_rate": 0.86},
                {"strategy": "Add print statements to debug iteration", "success_rate": 0.80},
                {"strategy": "Manually trace first 3 iterations", "success_rate": 0.85}
            ]
        }
        
        # Legacy pattern mapping for backward compatibility
        pattern_strategies = {
            "base_case_missing": [
                {"strategy": "Write base case first before recursive logic", "success_rate": 0.89},
                {"strategy": "Test with smallest input (n=0 or n=1)", "success_rate": 0.85},
                {"strategy": "Draw the recursion tree visually", "success_rate": 0.82}
            ],
            "stack_overflow": [
                {"strategy": "Check termination condition is reachable", "success_rate": 0.87},
                {"strategy": "Add debug prints to track call depth", "success_rate": 0.79},
                {"strategy": "Convert to iterative approach temporarily", "success_rate": 0.74}
            ],
            "off_by_one": [
                {"strategy": "Write loop boundaries on paper first", "success_rate": 0.88},
                {"strategy": "Test edge cases (empty, single element)", "success_rate": 0.84},
                {"strategy": "Use <= instead of < (or vice versa)", "success_rate": 0.76}
            ]
        }
        
        # Default fallback
        default_strategies = [
            {"strategy": "Break problem into smaller steps", "success_rate": 0.75},
            {"strategy": "Explain problem out loud", "success_rate": 0.71},
            {"strategy": "Draw diagrams/visualizations", "success_rate": 0.68},
            {"strategy": "Review similar solved examples", "success_rate": 0.73},
            {"strategy": "Practice with smaller test cases", "success_rate": 0.79}
        ]
        
        normalized_pattern = error_pattern.lower()
        
        # Try topic-specific strategies first
        for topic_key, strategies in topic_strategies.items():
            if topic_key in normalized_pattern:
                return strategies
        
        # Fall back to pattern-based strategies
        for pattern_key, strategies in pattern_strategies.items():
            if pattern_key in normalized_pattern:
                return strategies
        
        # Default fallback
        return default_strategies