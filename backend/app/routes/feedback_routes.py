# backend/app/routes/feedback_routes.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import re
from datetime import datetime
from uuid import uuid4

from app.models.memory_types import APIResponse, InteractionRecord, FeedbackRecord, InsightRecord
from app.services.llm_service import llm_service
from app.services.hindsight_service import hindsight_service
from app.engines.reflection_engine import reflection_engine


router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    user_id: str = Field("anonymous", description="Optional user id")
    user_query: str = Field(..., description="Original user query")
    llm_response: str = Field(..., description="Model response shown to user")
    engine_used: str = Field("orchestrator", description="Engine used to generate the response")
    feedback_text: str = Field(..., description="User feedback on response quality")
    rating: int = Field(..., ge=1, le=5, description="Feedback score from 1 to 5")
    interaction_id: Optional[str] = Field(None, description="Optional interaction id from client")
    understood: Optional[bool] = Field(None, description="Whether user understood response")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional confidence score")
    preferred_style: Optional[str] = Field(None, description="Optional preferred explanation style")
    topic: Optional[str] = Field(None, description="Topic/category of the interaction")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SuggestRequest(BaseModel):
    user_id: str = Field("anonymous", description="Optional user id")
    query: str = Field(..., description="Current user query")
    topic: Optional[str] = Field(None, description="Optional topic filter")
    limit: int = Field(15, ge=1, le=50, description="How many prior insights to analyze")


def _to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _infer_preferred_style(feedback_text: str, rating: int) -> str:
    text = feedback_text.lower()
    if "step" in text or "confusing" in text:
        return "step-by-step"
    if "example" in text or "practical" in text:
        return "example-driven"
    if "short" in text or "brief" in text:
        return "concise"
    if rating >= 4:
        return "current-style"
    return "guided"


def _build_structured_models(request: FeedbackRequest, reflection: Dict[str, Any]) -> Dict[str, Any]:
    interaction_id = request.interaction_id or str(uuid4())
    topic = (request.topic or "general").strip() or "general"

    interaction = InteractionRecord(
        interaction_id=interaction_id,
        user_id=request.user_id,
        query=request.user_query,
        response=request.llm_response,
        engine_used=request.engine_used,
        timestamp=datetime.utcnow()
    )

    understood = request.understood if request.understood is not None else request.rating >= 3

    base_conf = reflection.get("confidence", 0.7)
    try:
        base_conf = float(base_conf)
    except Exception:
        base_conf = 0.7

    confidence = request.confidence if request.confidence is not None else base_conf
    confidence = min(1.0, max(0.0, float(confidence)))

    feedback = FeedbackRecord(
        interaction_id=interaction_id,
        understood=understood,
        confidence=confidence,
        feedback_text=request.feedback_text
    )

    root_causes = reflection.get("root_causes") or []
    issue = str(root_causes[0]) if root_causes else "unclear_concept"
    preferred_style = request.preferred_style or _infer_preferred_style(request.feedback_text, request.rating)

    insight = InsightRecord(
        user_id=request.user_id,
        topic=topic,
        issue=issue,
        preferred_style=preferred_style,
        confidence_score=confidence,
        created_at=datetime.utcnow()
    )

    return {
        "interaction": interaction,
        "feedback": feedback,
        "insight": insight
    }


def _fallback_reflection(request: FeedbackRequest) -> Dict[str, Any]:
    sentiment = "positive" if request.rating >= 4 else "negative" if request.rating <= 2 else "neutral"

    if request.rating <= 2:
        action_items = [
            "Ask one clarifying question before answering.",
            "Provide a shorter, step-by-step explanation first, then detail.",
            "Add one concrete example aligned to the user query."
        ]
    elif request.rating == 3:
        action_items = [
            "Keep current response shape but improve precision and examples.",
            "Confirm assumptions explicitly in the first two lines."
        ]
    else:
        action_items = [
            "Preserve response style used in this interaction.",
            "Reuse successful explanation pattern for similar queries."
        ]

    return {
        "sentiment": sentiment,
        "root_causes": ["auto_inferred_from_rating_and_feedback"],
        "action_items": action_items,
        "confidence": 0.7,
        "summary": "Fallback reflection generated without LLM."
    }


def _parse_reflection_json(raw: str) -> Optional[Dict[str, Any]]:
    cleaned = raw.replace("<think>", "").replace("</think>", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(cleaned[start:end + 1])
    except Exception:
        return None


async def _reflect_feedback(request: FeedbackRequest) -> Dict[str, Any]:
    if not llm_service.available:
        return _fallback_reflection(request)

    prompt = f"""You are a reflection engine for improving future responses.

Given:
- User query: {request.user_query}
- Assistant response: {request.llm_response}
- User feedback text: {request.feedback_text}
- Rating (1-5): {request.rating}
- Topic: {request.topic or 'unknown'}

Return STRICT JSON with keys:
sentiment (positive|neutral|negative),
root_causes (array of short strings),
action_items (array of specific improvements),
confidence (0.0 to 1.0),
summary (one sentence)

Output JSON only.
"""

    raw = llm_service.generate(prompt, max_tokens=350, temperature=0.2)
    parsed = _parse_reflection_json(raw)

    if not parsed:
        return _fallback_reflection(request)

    sentiment = parsed.get("sentiment", "neutral")
    if sentiment not in {"positive", "neutral", "negative"}:
        sentiment = "neutral"

    root_causes = parsed.get("root_causes") or ["not_specified"]
    action_items = parsed.get("action_items") or ["Improve answer relevance to query intent."]

    try:
        confidence = float(parsed.get("confidence", 0.7))
    except Exception:
        confidence = 0.7

    confidence = min(1.0, max(0.0, confidence))

    return {
        "sentiment": sentiment,
        "root_causes": root_causes,
        "action_items": action_items,
        "confidence": confidence,
        "summary": parsed.get("summary", "Reflection generated from user feedback.")
    }


def _extract_feedback_insights(memories: list, topic: Optional[str] = None) -> list:
    insights = []

    for item in memories:
        if not isinstance(item, dict):
            continue

        content = str(item.get("content", ""))
        metadata = item.get("metadata") or item.get("context") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        insight_meta = metadata.get("insight") if isinstance(metadata.get("insight"), dict) else {}
        feedback_meta = metadata.get("feedback") if isinstance(metadata.get("feedback"), dict) else {}
        interaction_meta = metadata.get("interaction") if isinstance(metadata.get("interaction"), dict) else {}

        resolved_topic = insight_meta.get("topic", metadata.get("topic", "general"))
        memory_topic = str(resolved_topic).strip().lower()
        is_feedback_record = (
            metadata.get("type") == "feedback_reflection"
            or "feedback reflection" in content.lower()
        )

        if not is_feedback_record:
            continue

        if topic and topic.strip() and memory_topic and topic.strip().lower() != memory_topic:
            continue

        reflection = metadata.get("reflection")
        if not isinstance(reflection, dict):
            reflection = {
                "summary": content,
                "sentiment": "neutral",
                "action_items": []
            }

        insights.append({
            "id": item.get("id") or interaction_meta.get("interaction_id"),
            "interaction_id": interaction_meta.get("interaction_id"),
            "user_id": interaction_meta.get("user_id") or insight_meta.get("user_id", "anonymous"),
            "engine_used": interaction_meta.get("engine_used", "orchestrator"),
            "topic": resolved_topic,
            "issue": insight_meta.get("issue", "unclear_concept"),
            "preferred_style": insight_meta.get("preferred_style", "guided"),
            "rating": metadata.get("rating"),
            "understood": feedback_meta.get("understood"),
            "confidence": feedback_meta.get("confidence", insight_meta.get("confidence_score")),
            "feedback_text": feedback_meta.get("feedback_text", metadata.get("feedback_text", "")),
            "reflection": reflection,
            "timestamp": item.get("timestamp") or interaction_meta.get("timestamp")
        })

    return insights


async def _load_feedback_memories(topic: Optional[str], limit: int) -> Dict[str, Any]:
    demo_mode = True

    if hindsight_service.api_available and hindsight_service.client:
        query = "feedback reflection response quality learning signal"
        if topic:
            query = f"{query} {topic}"

        memories = await hindsight_service.client.recall(
            bank_id=hindsight_service.bank_id,
            query=query,
            max_tokens=4096
        )
        demo_mode = False
    else:
        memories = await hindsight_service.recall_all_memories(limit=limit * 3)

    return {
        "memories": memories,
        "demo_mode": demo_mode
    }


def _build_suggestion(query: str, topic: Optional[str], insights: list) -> Dict[str, Any]:
    if not insights:
        fallback_style = reflection_engine.extract_topic(query)
        return {
            "recommended_style": "guided",
            "recommended_actions": [
                "Ask one clarifying question first.",
                "Use step-by-step explanation with one concrete example."
            ],
            "top_issues": ["insufficient_feedback_history"],
            "target_topic": topic or fallback_style,
            "confidence": 0.55
        }

    style_counts: Dict[str, int] = {}
    issue_counts: Dict[str, int] = {}
    action_counts: Dict[str, int] = {}
    confidence_values = []

    for row in insights:
        style = str(row.get("preferred_style") or "guided")
        style_counts[style] = style_counts.get(style, 0) + 1

        issue = str(row.get("issue") or "unclear_concept")
        issue_counts[issue] = issue_counts.get(issue, 0) + 1

        conf = row.get("confidence")
        if isinstance(conf, (int, float)):
            confidence_values.append(float(conf))

        reflection = row.get("reflection")
        if isinstance(reflection, dict):
            for action in reflection.get("action_items", []):
                key = str(action).strip()
                if key:
                    action_counts[key] = action_counts.get(key, 0) + 1

    recommended_style = max(style_counts, key=style_counts.get)
    top_issues = sorted(issue_counts, key=issue_counts.get, reverse=True)[:3]
    recommended_actions = sorted(action_counts, key=action_counts.get, reverse=True)[:3]

    if not recommended_actions:
        recommended_actions = [
            "Use simpler wording and reduce abstraction.",
            "Include one worked example tied to the query."
        ]

    avg_conf = sum(confidence_values) / len(confidence_values) if confidence_values else 0.65

    return {
        "recommended_style": recommended_style,
        "recommended_actions": recommended_actions,
        "top_issues": top_issues,
        "target_topic": topic or reflection_engine.extract_topic(query),
        "confidence": min(1.0, max(0.0, avg_conf))
    }


def _normalize_user_insights(rows: list) -> list:
    """
    Normalize rows returned by hindsight_service.get_user_insights(user_id)
    into the same shape used by _build_suggestion.
    """
    normalized = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        data = row.get("data") if isinstance(row.get("data"), dict) else {}

        normalized.append(
            {
                "user_id": row.get("user_id", "anonymous"),
                "topic": data.get("topic", "general"),
                "issue": data.get("issue", "unclear_concept"),
                "preferred_style": data.get("preferred_style", "guided"),
                "confidence": data.get("confidence_score", 0.65),
                "reflection": {"action_items": data.get("action_items", [])},
                "timestamp": row.get("timestamp"),
            }
        )

    return normalized


def extract_topics(insights: List[Dict[str, Any]], limit: int = 5) -> List[str]:
    """Return most frequent weak topics based on issue-bearing insights.
    
    For new users (all insights are neutral), returns a meaningful baseline.
    """
    topic_counts: Dict[str, int] = {}
    has_real_issues = False

    for insight in insights:
        topic = str(insight.get("topic") or "general").strip().lower()
        issue = str(insight.get("issue") or "").strip().lower()

        if not topic or topic == "general":
            continue

        # Count topics that have real issues (not "none")
        if issue and issue not in {"resolved", "mastered", "none"}:
            has_real_issues = True
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        # For new users with no real issues, still count generic references
        elif issue == "none":
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # If we found real issues, filter to only those
    if has_real_issues:
        ordered = sorted(
            [(t, c) for t, c in topic_counts.items() if any(
                i.get("issue", "").lower() not in {"none", "resolved", "mastered"}
                for i in insights if i.get("topic", "").lower() == t
            )],
            key=lambda item: item[1],
            reverse=True
        )
    else:
        # For new users, return suggested learning areas (encouragement)
        ordered = sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)
        if not ordered:
            return ["[Start with any topic you want to learn!]"]

    return [topic for topic, _ in ordered[:limit]]


def calculate_improvement(insights: List[Dict[str, Any]]) -> float:
    """
    Compute confidence improvement percentage from earliest to latest insight.
    Returns a value in range [-100, 100].
    
    For new users, returns motivational value (start of journey).
    """
    confidence_values: List[float] = []

    for insight in insights:
        value = insight.get("confidence")
        if isinstance(value, (int, float)):
            confidence_values.append(float(value))

    if not confidence_values:
        return 0.0
    
    if len(confidence_values) == 1:
        # New user: show their baseline confidence as "ready to improve"
        return 5.0  # Small positive signal indicating room for growth
    
    # Multiple data points: calculate trend
    first = confidence_values[0]
    last = confidence_values[-1]
    improvement = (last - first) * 100.0
    return round(max(-100.0, min(100.0, improvement)), 2)


def extract_past_mistakes(insights: List[Dict[str, Any]], limit: int = 5) -> List[str]:
    """Return most repeated issue signals as past mistakes.
    
    For new users with no past mistakes, return encouraging message.
    """
    issue_counts: Dict[str, int] = {}

    for insight in insights:
        issue = str(insight.get("issue") or "").strip().lower()
        if not issue or issue in {"none", "resolved", "mastered"}:
            continue
        issue_counts[issue] = issue_counts.get(issue, 0) + 1

    ordered = sorted(issue_counts.items(), key=lambda item: item[1], reverse=True)
    if not ordered:
        return ["[No mistakes yet! You're starting fresh. Ready to learn? 🚀]"]
    
    return [issue for issue, _ in ordered[:limit]]


async def _get_learned_topics_from_hindsight(user_id: str) -> Dict[str, Any]:
    """
    Query Hindsight for actual studied memories to show what user has learned.
    Extracts topics from:
    - Study sessions (archaeology, quiz logs)
    - Interactions (questions asked, concepts explored)
    - Feedback sessions (topics user practiced)

    Returns: {
        "studied_topics": list of unique topics with confidence,
        "study_count": total interactions/sessions,
        "recent_topics": most recent topics studied,
        "high_confidence_topics": topics mastered
    }
    """
    try:
        if not hindsight_service.api_available or not hindsight_service.client:
            return {}

        # Recall user-scoped memories to extract study patterns
        memories = await hindsight_service.recall_all_memories(limit=150, user_id=user_id)

        if not memories:
            return {}

        topics_studied: Dict[str, Dict[str, Any]] = {}
        study_count = 0
        quiz_attempts = 0
        quiz_ratios: List[float] = []
        quiz_trend_points: List[Dict[str, Any]] = []
        seen_quiz_points = set()
        weak_topic_counts: Dict[str, int] = {}
        mistake_counts: Dict[str, int] = {}

        def _to_ratio(raw_metadata: Dict[str, Any]) -> Optional[float]:
            ratio = raw_metadata.get("quiz_score_ratio")
            score = raw_metadata.get("quiz_score")
            total = raw_metadata.get("quiz_total")
            try:
                if ratio is not None:
                    return max(0.0, min(1.0, float(ratio)))
                if score is not None and total is not None and float(total) > 0:
                    return max(0.0, min(1.0, float(score) / float(total)))
            except Exception:
                return None
            return None

        for memory in memories:
            if not isinstance(memory, dict):
                continue

            metadata = memory.get("metadata") if isinstance(memory.get("metadata"), dict) else {}
            context = memory.get("context") if isinstance(memory.get("context"), dict) else {}

            merged: Dict[str, Any] = {}
            merged.update(context)
            merged.update(metadata)

            # Filter for this user
            memory_user = str(merged.get("user_id") or "").strip()
            if memory_user and memory_user != user_id:
                continue

            content = str(memory.get("content") or memory.get("text") or "")

            # Extract topic from different sources
            topic = merged.get("topic") or merged.get("concept")

            if not topic and content:
                # Try to extract from content text
                if "topic:" in content.lower():
                    match = re.search(r"topic:\s*([a-zA-Z0-9_\s]+?)(?:\.|,|$)", content, re.IGNORECASE)
                    if match:
                        topic = match.group(1).strip()

                if not topic:
                    quiz_topic_match = re.search(
                        r"quiz\s+session\s+on\s+([a-zA-Z0-9_\-\s]{2,60}?)(?:\s+with\s+|\.|,|$)",
                        content,
                        flags=re.IGNORECASE,
                    )
                    if quiz_topic_match:
                        topic = quiz_topic_match.group(1).strip()

                if not topic:
                    score_topic_match = re.search(
                        r"on\s+([a-zA-Z0-9_\-\s]{2,60}?)\s+with\s+(?:a\s+)?(?:perfect\s+)?score",
                        content,
                        flags=re.IGNORECASE,
                    )
                    if score_topic_match:
                        topic = score_topic_match.group(1).strip()

            if topic and str(topic).strip().lower() not in {"general", "unknown", ""}:
                topic = str(topic).strip().lower()

                if topic not in topics_studied:
                    topics_studied[topic] = {
                        "count": 0,
                        "confidence_sum": 0.0,
                        "confidence_count": 0,
                        "last_studied": None,
                        "quiz_attempts": 0,
                        "quiz_ratio_sum": 0.0,
                    }

                topics_studied[topic]["count"] += 1
                study_count += 1

                # Update timestamp
                if "timestamp" in memory or "occurred_end" in memory or "mentioned_at" in memory:
                    topics_studied[topic]["last_studied"] = (
                        memory.get("timestamp")
                        or memory.get("occurred_end")
                        or memory.get("mentioned_at")
                    )

                # Update confidence from metadata if available
                confidence_candidates = [
                    merged.get("data_confidence"),
                    merged.get("confidence"),
                ]
                for conf_raw in confidence_candidates:
                    try:
                        if conf_raw is None:
                            continue
                        conf = max(0.0, min(1.0, float(conf_raw)))
                        topics_studied[topic]["confidence_sum"] += conf
                        topics_studied[topic]["confidence_count"] += 1
                        break
                    except Exception:
                        continue

                ratio_val = _to_ratio(merged)
                if ratio_val is None and content:
                    score_match = re.search(r"score\s+of\s+(\d+)\s*/\s*(\d+)", content, re.IGNORECASE)
                    if not score_match:
                        score_match = re.search(r"score\s*:\s*(\d+)\s*/\s*(\d+)", content, re.IGNORECASE)
                    if not score_match:
                        score_match = re.search(r"score\s+of\s+(\d+)\s+out\s+of\s+(\d+)", content, re.IGNORECASE)
                    if not score_match:
                        score_match = re.search(r"scor(?:e|ing)\s+(\d+)\s+out\s+of\s+(\d+)", content, re.IGNORECASE)
                    if score_match:
                        try:
                            score_val = float(score_match.group(1))
                            total_val = float(score_match.group(2))
                            ratio_val = (score_val / total_val) if total_val > 0 else None
                        except Exception:
                            ratio_val = None

                if ratio_val is None and content and "perfect score" in content.lower():
                    ratio_val = 1.0

                if ratio_val is not None:
                    point_timestamp = memory.get("timestamp") or memory.get("occurred_end") or memory.get("mentioned_at") or ""
                    point_key = f"{topic}|{point_timestamp}|{round(float(ratio_val), 3)}"

                    if point_key in seen_quiz_points:
                        continue
                    seen_quiz_points.add(point_key)

                    quiz_attempts += 1
                    quiz_ratios.append(ratio_val)
                    quiz_trend_points.append(
                        {
                            "timestamp": point_timestamp,
                            "ratio": ratio_val,
                        }
                    )

                    topics_studied[topic]["quiz_attempts"] += 1
                    topics_studied[topic]["quiz_ratio_sum"] += ratio_val

                    if ratio_val <= 0.67:
                        weak_topic_counts[topic] = weak_topic_counts.get(topic, 0) + 1

                mistakes_raw = merged.get("quiz_mistakes")
                if mistakes_raw:
                    parsed_mistakes: List[str] = []
                    if isinstance(mistakes_raw, list):
                        parsed_mistakes = [str(item).strip() for item in mistakes_raw if str(item).strip()]
                    elif isinstance(mistakes_raw, str):
                        try:
                            parsed = json.loads(mistakes_raw)
                            if isinstance(parsed, list):
                                parsed_mistakes = [str(item).strip() for item in parsed if str(item).strip()]
                            elif mistakes_raw.strip():
                                parsed_mistakes = [mistakes_raw.strip()]
                        except Exception:
                            if mistakes_raw.strip():
                                parsed_mistakes = [mistakes_raw.strip()]

                    for mistake in parsed_mistakes:
                        mistake_counts[mistake] = mistake_counts.get(mistake, 0) + 1

                weak_area = str(merged.get("weak_area") or "").strip().lower()
                if not weak_area and content:
                    weak_area_match = re.search(r"'([^']{2,80})'\s+as\s+(?:a\s+)?weak\s+area", content, re.IGNORECASE)
                    if not weak_area_match:
                        weak_area_match = re.search(r"mistake\s+related\s+to\s+the\s+'([^']{2,80})'", content, re.IGNORECASE)
                    if weak_area_match:
                        weak_area = weak_area_match.group(1).strip().lower()

                if weak_area and weak_area not in {"none", "unknown", "general"}:
                    mistake_counts[weak_area] = mistake_counts.get(weak_area, 0) + 1
                    weak_topic_counts[topic] = weak_topic_counts.get(topic, 0) + 1

        # Sort by frequency
        sorted_topics = sorted(
            topics_studied.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        topic_mastery: Dict[str, float] = {}
        for topic, stats in sorted_topics:
            confidence_count = int(stats.get("confidence_count", 0) or 0)
            confidence_sum = float(stats.get("confidence_sum", 0.0) or 0.0)
            ratio_attempts = int(stats.get("quiz_attempts", 0) or 0)
            ratio_sum = float(stats.get("quiz_ratio_sum", 0.0) or 0.0)

            confidence_avg = (confidence_sum / confidence_count) if confidence_count > 0 else 0.0
            ratio_avg = (ratio_sum / ratio_attempts) if ratio_attempts > 0 else 0.0

            if ratio_attempts > 0 and confidence_count > 0:
                mastery = (confidence_avg + ratio_avg) / 2.0
            elif ratio_attempts > 0:
                mastery = ratio_avg
            elif confidence_count > 0:
                mastery = confidence_avg
            else:
                mastery = 0.5

            topic_mastery[topic] = round(max(0.0, min(1.0, mastery)), 3)

        high_confidence_topics = [topic for topic, score in topic_mastery.items() if score >= 0.78]

        recent_topics = [
            t[0]
            for t in sorted(
                topics_studied.items(),
                key=lambda item: str(item[1].get("last_studied") or ""),
                reverse=True,
            )[:3]
        ]

        weak_topics = [
            topic
            for topic, _ in sorted(weak_topic_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        ]

        quiz_improvement_score = 0.0
        if len(quiz_trend_points) >= 2:
            ordered = sorted(quiz_trend_points, key=lambda item: str(item.get("timestamp") or ""))
            first = float(ordered[0]["ratio"])
            last = float(ordered[-1]["ratio"])
            quiz_improvement_score = round((last - first) * 100.0, 2)

        avg_quiz_ratio = round(sum(quiz_ratios) / len(quiz_ratios), 3) if quiz_ratios else 0.0
        past_mistakes = [
            issue for issue, _ in sorted(mistake_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        ]

        result = {
            "studied_topics": [t[0] for t in sorted_topics[:10]],
            "study_count": study_count,
            "recent_topics": recent_topics,
            "high_confidence_topics": high_confidence_topics,
            "weak_topics": weak_topics,
            "past_mistakes": past_mistakes,
            "quiz_attempts": quiz_attempts,
            "avg_quiz_score_ratio": avg_quiz_ratio,
            "quiz_improvement_score": quiz_improvement_score,
            "topic_mastery": topic_mastery,
        }

        return result

    except Exception as e:
        print(f"[WARNING] Failed to get learned topics from Hindsight: {e}")
        return {}


@router.get("/insights", response_model=APIResponse)
async def get_feedback_insights(
    limit: int = Query(10, ge=1, le=50, description="Maximum feedback insights to return"),
    topic: Optional[str] = Query(None, description="Optional topic filter")
):
    """
    Retrieve previously reflected feedback insights so the orchestrator can
    reuse learning signals for future responses.
    """
    try:
        fetch_result = await _load_feedback_memories(topic=topic, limit=limit)
        memories = fetch_result["memories"]
        demo_mode = fetch_result["demo_mode"]

        insights = _extract_feedback_insights(memories, topic=topic)[:limit]

        return APIResponse(
            status="success",
            data={
                "count": len(insights),
                "insights": insights,
                "orchestrator_stage": "feedback_insights_recalled"
            },
            demo_mode=demo_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest", response_model=APIResponse)
async def suggest_response_strategy(request: SuggestRequest):
    """
    Suggest response strategy for current query using stored feedback insights.
    Additive helper for orchestrator decision-making.
    """
    try:
        # Prefer user-specific structured insights if available.
        user_insight_rows = await hindsight_service.get_user_insights(request.user_id)
        normalized_user_insights = _normalize_user_insights(user_insight_rows)

        fetch_result = await _load_feedback_memories(topic=request.topic, limit=request.limit)
        memories = fetch_result["memories"]
        demo_mode = fetch_result["demo_mode"]

        all_insights = _extract_feedback_insights(memories, topic=request.topic)
        user_scoped = [item for item in all_insights if item.get("user_id") == request.user_id]
        source_insights = normalized_user_insights or (user_scoped if user_scoped else all_insights)

        suggestion = _build_suggestion(
            query=request.query,
            topic=request.topic,
            insights=source_insights[: request.limit],
        )

        return APIResponse(
            status="success",
            data={
                "orchestrator_stage": "response_strategy_suggested",
                "user_id": request.user_id,
                "query": request.query,
                "suggestion": suggestion,
                "evidence_count": len(source_insights[: request.limit])
            },
            demo_mode=demo_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-progress", response_model=APIResponse)
async def get_progress(
    user_id: str = Query(..., description="User ID for progress tracking"),
    topic: str = Query(None, description="Optional topic to filter progress by"),
):
    # Get user insights for weak topics and improvement
    insights = await hindsight_service.get_user_insights(user_id)
    normalized = _normalize_user_insights(insights)
    
    # Get actual studied topics from Hindsight memories
    learned_topics_data = await _get_learned_topics_from_hindsight(user_id)
    studied_topics = learned_topics_data.get("studied_topics", [])
    
    # Filter by topic if provided
    if topic and topic.strip():
        topic_lower = topic.strip().lower()
        normalized = [
            n for n in normalized
            if str(n.get("topic", "general")).strip().lower() == topic_lower
        ]

    base_weak_topics = extract_topics(normalized)
    memory_weak_topics = learned_topics_data.get("weak_topics", []) if isinstance(learned_topics_data.get("weak_topics"), list) else []
    weak_topics = memory_weak_topics or base_weak_topics

    base_past_mistakes = extract_past_mistakes(normalized)
    memory_past_mistakes = learned_topics_data.get("past_mistakes", []) if isinstance(learned_topics_data.get("past_mistakes"), list) else []
    merged_past_mistakes: List[str] = []
    for item in memory_past_mistakes + base_past_mistakes:
        item_str = str(item).strip()
        if not item_str:
            continue
        if item_str.lower() in {m.lower() for m in merged_past_mistakes}:
            continue
        merged_past_mistakes.append(item_str)

    confidence_improvement = calculate_improvement(normalized)
    quiz_improvement = learned_topics_data.get("quiz_improvement_score")
    quiz_attempts = int(learned_topics_data.get("quiz_attempts", 0) or 0)
    if isinstance(quiz_improvement, (int, float)) and quiz_attempts > 0:
        # Prefer quiz-grounded trend; blend with confidence trend when both exist.
        improvement_score = (
            round((0.7 * float(quiz_improvement)) + (0.3 * confidence_improvement), 2)
            if normalized
            else round(float(quiz_improvement), 2)
        )
    else:
        improvement_score = confidence_improvement

    return APIResponse(
        status="success",
        data={
            "user_id": user_id,
            "topic": topic or "all",
            "weak_topics": weak_topics,
            "studied_topics": studied_topics,
            "recent_topics": learned_topics_data.get("recent_topics", []),
            "high_confidence_topics": learned_topics_data.get("high_confidence_topics", []),
            "improvement_score": improvement_score,
            "past_mistakes": merged_past_mistakes[:5],
            "insights_count": len(normalized),
            "study_sessions_count": learned_topics_data.get("study_count", 0),
            "quiz_attempts": quiz_attempts,
            "avg_quiz_score_ratio": learned_topics_data.get("avg_quiz_score_ratio", 0.0),
            "quiz_improvement_score": learned_topics_data.get("quiz_improvement_score", 0.0),
            "topic_mastery": learned_topics_data.get("topic_mastery", {}),
            "orchestrator_stage": "user_progress_computed",
            # NEW: Guide users to enhanced memory visualizations
            "view_impressive_memory_features": {
                "timeline_url": f"/memory/timeline?user_id={user_id}",
                "confidence_graph_url": f"/memory/timeline?user_id={user_id}",
                "learning_profile_url": f"/memory/what-cogni-knows?user_id={user_id}",
                "insight": "Visit /memory/timeline for learning progression & /memory/what-cogni-knows for your personalized learning profile!"
            }
        },
        demo_mode=bool(insights and insights[0].get("demo_mode")) if isinstance(insights, list) else True,
    )


@router.post("/log", response_model=APIResponse)
async def log_feedback(request: FeedbackRequest):
    """
    Additive feedback pipeline:
    User Feedback -> Reflection -> Structured Insights -> Hindsight Memory.

    This route does not modify existing feature routes and is safe to add in-between
    current flows.
    """
    try:
        reflection = await _reflect_feedback(request)
        models = _build_structured_models(request, reflection)

        interaction = models["interaction"]
        feedback = models["feedback"]
        insight = models["insight"]

        rule_based_insights = reflection_engine.analyze(
            interaction={
                "query": interaction.query,
                "response": interaction.response,
                "engine_used": interaction.engine_used,
                "user_id": interaction.user_id,
            },
            feedback={
                "understood": feedback.understood,
                "confidence": feedback.confidence,
                "feedback_text": feedback.feedback_text,
            },
        )

        insight_payload = {
            "type": "feedback_reflection",
            "topic": insight.topic,
            "rating": request.rating,
            "feedback_text": feedback.feedback_text,
            "interaction": _to_dict(interaction),
            "feedback": _to_dict(feedback),
            "insight": _to_dict(insight),
            "reflection": reflection,
            "rule_based_insights": rule_based_insights,
            "metadata": request.metadata or {}
        }

        memory_content = (
            f"Feedback reflection for interaction={interaction.interaction_id} | "
            f"topic={insight.topic} | issue={insight.issue} | "
            f"sentiment={reflection.get('sentiment')}"
        )

        memory_result = await hindsight_service.retain_study_session(
            content=memory_content,
            context=insight_payload
        )

        # Also store as first-class insight record for direct retrieval.
        persisted_insight = {
            **_to_dict(insight),
            "action_items": reflection.get("action_items", []),
            "sentiment": reflection.get("sentiment", "neutral"),
        }
        insight_store_result = await hindsight_service.store_insight(
            user_id=request.user_id,
            insight=persisted_insight,
        )

        return APIResponse(
            status="success",
            data={
                "orchestrator_stage": "feedback_logged",
                "interaction": _to_dict(interaction),
                "feedback": _to_dict(feedback),
                "insight": _to_dict(insight),
                "structured_insights": reflection,
                "rule_based_insights": rule_based_insights,
                "memory_status": memory_result,
                "insight_store_status": insight_store_result,
                "future_response_improved": True
            },
            demo_mode=memory_result.get("demo_mode", True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
