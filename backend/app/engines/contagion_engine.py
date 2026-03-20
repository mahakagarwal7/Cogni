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
    
    async def get_community_insights(self, error_pattern: str) -> Dict[str, Any]:
        """
        Get insights personalized to THIS student's learning history.
        Uses Hindsight to query actual peer data for the specific topic/input.
        Treats error_pattern as topic internally and generates a learning plan.
        
        Pipeline:
        1. Query Hindsight for peer data on this specific topic
        2. Recall student's personal learning history
        3. Generate topic-specific strategies using LLM
        4. Generate mentor-guided learning plan
        5. Return personalized recommendations (backward compatible)
        """
        # UPGRADE: Treat error_pattern as topic internally
        topic = error_pattern
        
        # Step 1: Query Hindsight for peer insights on THIS TOPIC
        hindsight_data = await self.hindsight.recall_global_contagion(topic)
        
        # Step 2: Recall THIS STUDENT'S learning history
        student_memories = await self.hindsight.recall_all_memories(limit=20)
        personal_context = await self._extract_personal_patterns(
            student_memories=student_memories,
            error_pattern=topic
        )
        
        # Step 3: Generate topic-specific strategies using LLM + Hindsight data
        strategies = await self._generate_topic_strategies(
            topic=topic,
            personal_context=personal_context,
            hindsight_data=hindsight_data
        )
        
        # Step 4: Refine using LLM for personalization
        refined_result = await self._refine_for_student(
            error_pattern=topic,
            strategies=strategies,
            personal_context=personal_context
        )
        
        # UPGRADE: Generate learning plan (NEW)
        peer_strategies = hindsight_data.get("top_strategy", "")
        learning_plan = await self._generate_learning_plan(
            topic=topic,
            peer_strategies=peer_strategies,
            personal_context=personal_context
        )
        
        # Step 5: Build response (EXACT same format - backward compatible + NEW learning_plan)
        return {
            "feature": "metacognitive_contagion",
            "error_pattern": error_pattern,
            "community_size": hindsight_data.get("community_size", 0),
            "top_strategy": refined_result.get("top_strategy", self._generate_default_strategy(topic)),
            "success_rate": refined_result.get("success_rate", 0.79),
            "privacy_note": "Personalized based on your learning history + peer patterns",
            "additional_strategies": refined_result.get("strategies", []),
            "learning_plan": learning_plan,  # UPGRADE: NEW FIELD (safe to add)
            "demo_mode": hindsight_data.get("demo_mode", True)
        }
    
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
    
    async def _generate_topic_strategies(
        self,
        topic: str,
        personal_context: Dict[str, Any],
        hindsight_data: Dict[str, Any]
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
            
            prompt = f"""Generate 4 SPECIFIC, ACTIONABLE strategies for learning/mastering "{topic}".

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
        
        # Priority 4: Generic fallback strategies
        fallback = [
            {
                "strategy": f"Start with fundamental concepts in {topic}",
                "success_rate": 0.80,
                "source": "fallback"
            },
            {
                "strategy": f"Practice problems related to {topic} progressively",
                "success_rate": 0.82,
                "source": "fallback"
            },
            {
                "strategy": f"Study peer solutions and approaches to {topic}",
                "success_rate": 0.78,
                "source": "fallback"
            },
            {
                "strategy": f"Build a project or apply {topic} in real scenarios",
                "success_rate": 0.85,
                "source": "fallback"
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
        personal_context: Dict[str, Any]
    ) -> str:
        """
        UPGRADE: Generate a mentor-guided learning plan for the topic using LLM.
        
        Returns a clean, readable roadmap with 4-6 steps.
        Each step explains WHAT to do and WHY.
        No percentages, bullet symbols, or meta explanations.
        """
        if not self.llm.available:
            # Safe fallback
            return f"Start learning {topic} by breaking it into smaller concepts and practicing step-by-step."
        
        # Build context
        learning_style = personal_context.get("learning_style", "adaptive")
        peer_benefit = f" What helped others: {peer_strategies}." if peer_strategies else ""
        
        prompt = f"""You are a mentor creating a personalized learning roadmap.

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
            if not final_plan or len(final_plan) < 50:
                return f"Start learning {topic} by breaking it into smaller concepts and practicing step-by-step."
            
            return final_plan
            
        except Exception as e:
            print(f"[DEBUG] Learning plan generation failed: {e}")
            return f"Start learning {topic} by breaking it into smaller concepts and practicing step-by-step."
    
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
        personal_context: Dict[str, Any]
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
        prompt = f"""Based on this student's learning history, rank these strategies for: "{error_pattern}"

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