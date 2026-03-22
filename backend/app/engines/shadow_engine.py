
"""
👤 Feature 3: Cognitive Shadow
Your digital twin predicts where you'll struggle next.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.services.llm_service import llm_service
from typing import Dict, Any, List, Optional
import json

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

    def _topic_tokens(self, topic: str) -> List[str]:
        normalized = topic.lower().replace("_", " ").replace("-", " ").replace("/", " ").strip()
        return [t for t in normalized.split() if len(t) > 2]

    def _is_topic_related(self, text: str, topic: str) -> bool:
        text_lower = str(text).lower()
        topic_lower = str(topic).lower().strip()
        if not topic_lower:
            return True
        if topic_lower in text_lower:
            return True
        tokens = self._topic_tokens(topic_lower)
        if not tokens:
            return True
        return any(token in text_lower for token in tokens)

    def _filter_synthesis_for_topic(self, synthesis: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Filter hindsight synthesis to topic-related signals to avoid drift."""
        if not isinstance(synthesis, dict):
            return {"recent_topics": [topic] if topic else [], "evidence": []}

        raw_topics = synthesis.get("recent_topics") if isinstance(synthesis.get("recent_topics"), list) else []
        raw_evidence = synthesis.get("evidence") if isinstance(synthesis.get("evidence"), list) else []

        filtered_topics = [str(t) for t in raw_topics if isinstance(t, str) and self._is_topic_related(t, topic)]
        if topic and not any(str(t).lower().strip() == topic.lower().strip() for t in filtered_topics):
            filtered_topics.insert(0, topic)

        filtered_evidence = [str(e) for e in raw_evidence if isinstance(e, str) and self._is_topic_related(e, topic)]
        if not filtered_evidence and raw_evidence:
            # Keep at most one global signal if no direct topic evidence exists.
            filtered_evidence = [str(raw_evidence[0])]

        return {
            "prediction": synthesis.get("prediction"),
            "confidence": synthesis.get("confidence", 0.75),
            "evidence": filtered_evidence,
            "recent_topics": filtered_topics[:5],
            "demo_mode": synthesis.get("demo_mode", False),
        }

    def analyzeTopicDepth(self, context: Dict[str, Any], hindsightData: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze topic depth, subtopics, difficulty, and known gaps from context + hindsight."""
        topic = str(context.get("current_topic") or "general").strip() or "general"
        topic_tokens = self._topic_tokens(topic)

        synthesis = hindsightData.get("synthesis") if isinstance(hindsightData.get("synthesis"), dict) else {}
        recent_topics = synthesis.get("recent_topics") if isinstance(synthesis.get("recent_topics"), list) else []
        evidence = synthesis.get("evidence") if isinstance(synthesis.get("evidence"), list) else []
        insights = hindsightData.get("insights") if isinstance(hindsightData.get("insights"), list) else []

        related_topics = [str(t) for t in recent_topics if isinstance(t, str) and t.strip() and self._is_topic_related(t, topic)]
        unique_related_topics: List[str] = []
        for item in related_topics:
            lowered = item.lower()
            if lowered not in [x.lower() for x in unique_related_topics]:
                unique_related_topics.append(item)

        weak_signals = [
            str(ev)
            for ev in evidence
            if isinstance(ev, str)
            and self._is_topic_related(ev, topic)
            and any(k in ev.lower() for k in ["weak", "struggle", "quiz weakness", "mistake", "confus"])
        ]

        known_gaps: List[str] = []
        for insight in insights[:10]:
            if not isinstance(insight, dict):
                continue
            data = insight.get("data") if isinstance(insight.get("data"), dict) else {}
            issue = str(data.get("issue", "")).strip()
            topic_name = str(data.get("topic", "")).strip()
            if issue:
                if topic_name and self._is_topic_related(topic_name, topic):
                    known_gaps.append(f"{topic_name}: {issue}")
                elif not topic_name:
                    known_gaps.append(issue)
            if len(known_gaps) >= 5:
                break

        signal_count = len(weak_signals) + len(known_gaps)
        if signal_count >= 5:
            difficulty_level = "hard"
        elif signal_count >= 2:
            difficulty_level = "medium"
        else:
            difficulty_level = "easy"

        subtopics = unique_related_topics[:4]
        if not subtopics and topic_tokens:
            subtopics = [" ".join(topic_tokens[:2])]

        return {
            "topic": topic,
            "subtopics": subtopics,
            "difficulty_level": difficulty_level,
            "known_gaps": known_gaps,
            "weak_signals": weak_signals,
            "recent_topics": unique_related_topics[:5],
        }

    def _build_prediction_fallbacks(self, topic_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Deterministic prediction cards from hindsight-derived topic analysis."""
        topic = str(topic_analysis.get("topic", "general"))
        weak_signals = topic_analysis.get("weak_signals") if isinstance(topic_analysis.get("weak_signals"), list) else []
        known_gaps = topic_analysis.get("known_gaps") if isinstance(topic_analysis.get("known_gaps"), list) else []
        subtopics = topic_analysis.get("subtopics") if isinstance(topic_analysis.get("subtopics"), list) else []
        difficulty = str(topic_analysis.get("difficulty_level", "medium")).capitalize()

        cards: List[Dict[str, Any]] = []

        first_gap = str(known_gaps[0]) if known_gaps else f"foundational understanding in {topic}"
        cards.append({
            "title": f"Foundation Drift in {topic}",
            "description": f"You may lose accuracy when {first_gap} is needed across steps.",
            "trigger_condition": f"When problems combine multiple concepts inside {topic}.",
            "suggested_micro_action": "Write one-line definitions before solving and verify each step.",
            "difficulty": difficulty,
            "confidence": 0.78,
        })

        jump_target = str(subtopics[0]) if subtopics and self._is_topic_related(str(subtopics[0]), topic) else topic
        cards.append({
            "title": "Conceptual Jump Overload",
            "description": f"Switching between idea and execution in {jump_target} may create confusion.",
            "trigger_condition": "When moving from theory to applied questions quickly.",
            "suggested_micro_action": "Do one mini example first, then scale to a full problem.",
            "difficulty": "Medium",
            "confidence": 0.74,
        })

        signal_hint = str(weak_signals[0]) if weak_signals else "past weak-topic trend"
        cards.append({
            "title": "Repeated Mistake Pattern",
            "description": f"Hindsight indicates recurring friction: {signal_hint}.",
            "trigger_condition": f"When similar {topic} patterns appear under time pressure.",
            "suggested_micro_action": "Pause for 20 seconds and check assumptions before finalizing.",
            "difficulty": "Hard" if difficulty == "Hard" else "Medium",
            "confidence": 0.76,
        })

        # Keep 3-5 predictions.
        return cards[:5]

    def _parse_prediction_json(self, raw: str) -> List[Dict[str, Any]]:
        """Extract prediction list from model output safely."""
        cleaned = raw.replace("<think>", "").replace("</think>", "").strip()
        if not cleaned:
            return []

        # Attempt JSON object extraction first.
        candidate = cleaned
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start:end + 1]

        try:
            parsed = json.loads(candidate)
        except Exception:
            return []

        if not isinstance(parsed, dict):
            return []
        predictions = parsed.get("predictions")
        if not isinstance(predictions, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in predictions[:5]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            description = str(item.get("description", "")).strip()
            trigger_condition = str(item.get("trigger_condition", "")).strip()
            suggested_micro_action = str(item.get("suggested_micro_action", "")).strip()
            if not (title and description and trigger_condition and suggested_micro_action):
                continue
            normalized.append({
                "title": title,
                "description": description,
                "trigger_condition": trigger_condition,
                "suggested_micro_action": suggested_micro_action,
                "difficulty": str(item.get("difficulty", "Medium")).strip() or "Medium",
                "confidence": float(item.get("confidence", 0.74)) if str(item.get("confidence", "")).strip() else 0.74,
            })
        return normalized

    def generatePredictions(self, topic_analysis: Dict[str, Any], hindsightData: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate 3-5 personalized struggle predictions using hindsight-first strategy with LLM refinement."""
        fallback_cards = self._build_prediction_fallbacks(topic_analysis)
        if not fallback_cards:
            return []

        if not self.llm.available:
            return fallback_cards

        synthesis = hindsightData.get("synthesis") if isinstance(hindsightData.get("synthesis"), dict) else {}
        insights = hindsightData.get("insights") if isinstance(hindsightData.get("insights"), list) else []
        memory_context = self._format_insights(insights)
        evidence = synthesis.get("evidence") if isinstance(synthesis.get("evidence"), list) else []
        evidence_text = "\n".join([f"- {str(ev)}" for ev in evidence[:5]]) if evidence else "- limited evidence"

        prompt = f"""You are upgrading a predictive learning mentor.
Use hindsight evidence as the PRIMARY source; use reasoning only to refine.

Current topic analysis:
{json.dumps(topic_analysis, ensure_ascii=False)}

Hindsight evidence:
{evidence_text}

User insight summary:
{memory_context}

Task:
Produce 3 to 5 predictions about next likely struggles for this user.
Each prediction must include:
- title
- description
- trigger_condition
- suggested_micro_action
- difficulty (Easy/Medium/Hard)
- confidence (0.0 to 1.0)

Rules:
- Keep each prediction strongly tied to topic: {topic_analysis.get('topic', 'general')}
- Avoid generic statements.
- No direct answers; only anticipatory guidance.
- Return ONLY valid JSON in this format:
{{"predictions":[{{"title":"...","description":"...","trigger_condition":"...","suggested_micro_action":"...","difficulty":"Medium","confidence":0.76}}]}}"""

        try:
            raw = self.llm.generate(prompt, max_tokens=500, temperature=0.35)
            parsed = self._parse_prediction_json(raw)
            if parsed:
                topic = str(topic_analysis.get("topic", "general"))
                aligned = [
                    row for row in parsed
                    if self._is_topic_related(
                        " ".join([
                            str(row.get("title", "")),
                            str(row.get("description", "")),
                            str(row.get("trigger_condition", "")),
                        ]),
                        topic,
                    )
                ]
                if aligned:
                    return aligned[:5]
        except Exception as e:
            print(f"[DEBUG] Shadow prediction LLM refinement skipped: {e}")

        return fallback_cards

    def predictStruggles(self, context: Dict[str, Any], hindsightData: Dict[str, Any]) -> Dict[str, Any]:
        """Top-level modular predictor: context understanding + prediction generation."""
        topic_analysis = self.analyzeTopicDepth(context, hindsightData)
        predictions = self.generatePredictions(topic_analysis, hindsightData)

        # Deduplicate by title while preserving order.
        unique_predictions: List[Dict[str, Any]] = []
        seen_titles = set()
        for row in predictions:
            title_key = str(row.get("title", "")).lower().strip()
            if not title_key or title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            unique_predictions.append(row)

        final_predictions = unique_predictions[:5]
        if len(final_predictions) < 3:
            for row in self._build_prediction_fallbacks(topic_analysis):
                title_key = str(row.get("title", "")).lower().strip()
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    final_predictions.append(row)
                if len(final_predictions) >= 3:
                    break

        primary_prediction = final_predictions[0]["description"] if final_predictions else f"Monitor weak spots while advancing in {topic_analysis.get('topic', 'the topic')}."

        return {
            "topic_analysis": topic_analysis,
            "predictions": final_predictions,
            "prediction_summary": primary_prediction,
        }
    
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
            synthesis = self._filter_synthesis_for_topic(synthesis, current_topic)
            next_challenge = self.hindsight._predict_next_challenge([current_topic], [])
            insights = await self.hindsight.get_user_insights(user_id)
            struggle_bundle = self.predictStruggles(
                context={
                    "current_topic": current_topic,
                    "user_id": user_id,
                    "days": days,
                },
                hindsightData={
                    "synthesis": synthesis,
                    "insights": insights,
                },
            )
            predictions = struggle_bundle.get("predictions") if isinstance(struggle_bundle.get("predictions"), list) else []
            top_prediction = predictions[0] if predictions else {}
            prediction_text = str(top_prediction.get("description") or synthesis.get("prediction") or next_challenge["prediction"])
            result = {
                "response_id": response_id,
                "feature": "cognitive_shadow",
                "prediction": prediction_text,
                "confidence": min(next_challenge["confidence"] + 0.1, 0.95),  # Boost confidence for current topic
                "evidence": synthesis.get("evidence", next_challenge["evidence"]),
                "current_topic": current_topic,
                "recent_topics": synthesis.get("recent_topics", [current_topic]),
                "predictions": predictions,
                "topic_analysis": struggle_bundle.get("topic_analysis", {}),
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
                    "confidence": result["confidence"],
                    "predictions_count": len(predictions),
                }
            )
            
            return result
        
        # Priority 2: Query Hindsight for conversation history
        from uuid import uuid4
        response_id = str(uuid4())
        prediction = await self.hindsight.reflect_cognitive_shadow(days=days, user_id=user_id)
        insights = await self.hindsight.get_user_insights(user_id)
        memory_context = self._format_insights(insights)

        inferred_topic = current_topic or (
            prediction.get("recent_topics", [None])[0] if isinstance(prediction.get("recent_topics"), list) and prediction.get("recent_topics") else "general"
        )
        struggle_bundle = self.predictStruggles(
            context={
                "current_topic": inferred_topic,
                "user_id": user_id,
                "days": days,
            },
            hindsightData={
                "synthesis": prediction,
                "insights": insights,
            },
        )
        predictions = struggle_bundle.get("predictions") if isinstance(struggle_bundle.get("predictions"), list) else []
        
        # Optionally use LLM to enhance the prediction text
        prediction_text = prediction.get("prediction", "Keep practicing consistently")
        recent_topics = prediction.get("recent_topics", [])
        if predictions:
            prediction_text = str(predictions[0].get("description", prediction_text))
        
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
            "predictions": predictions,
            "topic_analysis": struggle_bundle.get("topic_analysis", {}),
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
                "topics_count": len(recent_topics),
                "predictions_count": len(predictions),
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