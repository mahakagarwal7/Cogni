# backend/app/routes/study_routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.engines.archaeology_engine import ArchaeologyEngine
from app.models.memory_types import StudySession, APIResponse, QuizSubmission
from app.services.hindsight_service import hindsight_service
from app.services.llm_service import llm_service
import json
import re

router = APIRouter(prefix="/study", tags=["study"])

# Dependency injection for engine
def get_archaeology_engine():
    return ArchaeologyEngine()


def _fallback_quiz(topic: str) -> list[dict]:
    return [
        {
            "id": 1,
            "question": f"What is the core idea behind {topic}?",
            "expected_answer": f"A concise definition of {topic} and why it matters.",
        },
        {
            "id": 2,
            "question": f"Give one common mistake students make in {topic}.",
            "expected_answer": "A concrete misconception and how to avoid it.",
        },
        {
            "id": 3,
            "question": f"How would you apply {topic} in a practical problem?",
            "expected_answer": "One practical scenario and the first step to solve it.",
        },
    ]


def _safe_parse_quiz_json(raw: str, topic: str) -> list[dict]:
    cleaned = raw.replace("<think>", "").replace("</think>", "").strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return _fallback_quiz(topic)

    try:
        parsed = json.loads(cleaned[start:end + 1])
    except Exception:
        return _fallback_quiz(topic)

    questions = []
    for idx, row in enumerate(parsed[:3], start=1):
        if not isinstance(row, dict):
            continue
        q = str(row.get("question", "")).strip()
        a = str(row.get("expected_answer", "")).strip()
        if q and a:
            questions.append({"id": idx, "question": q, "expected_answer": a})

    return questions if len(questions) == 3 else _fallback_quiz(topic)


def _normalize_answer(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())

@router.post("/log", response_model=APIResponse)
async def log_study_session(
    session: StudySession,
    engine: ArchaeologyEngine = Depends(get_archaeology_engine)
):
    """
    POST /api/study/log
    Save a new study session to memory.
    """
    try:
        result = await engine.log_study_session(session)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/archaeology", response_model=APIResponse)
async def get_temporal_archaeology(
    topic: str,
    confusion_level: int,
    days: Optional[int] = 30,
    user_id: str = Query("student", description="User ID for memory tracking"),
    engine: ArchaeologyEngine = Depends(get_archaeology_engine)
):
    """
    GET /api/study/archaeology?topic=recursion&confusion_level=4&user_id=student
    Feature 1: Find when you last felt this confused + what helped.
    """
    if not (1 <= confusion_level <= 5):
        raise HTTPException(status_code=400, detail="confusion_level must be 1-5")
    
    try:
        result = await engine.find_past_struggles(topic, confusion_level, days, user_id)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("result", {}).get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quiz", response_model=APIResponse)
async def generate_quiz(
    topic: str = Query(..., description="Topic for quiz generation"),
    user_id: str = Query("student", description="User ID for personalization"),
):
    """
    Generate a simple 3-question revision quiz.
    Additive endpoint: does not affect existing routes.
    """
    try:
        if llm_service.available:
            prompt = f"""Generate exactly 3 short revision questions for topic: {topic}.
Return JSON array only in this format:
[
  {{"question":"...", "expected_answer":"..."}},
  {{"question":"...", "expected_answer":"..."}},
  {{"question":"...", "expected_answer":"..."}}
]
No extra text."""
            raw = llm_service.generate(prompt, max_tokens=450, temperature=0.3)
            questions = _safe_parse_quiz_json(raw, topic)
        else:
            questions = _fallback_quiz(topic)

        return APIResponse(
            status="success",
            data={
                "topic": topic,
                "user_id": user_id,
                "questions": questions,
                "total_questions": len(questions),
            },
            demo_mode=not llm_service.available,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quiz/submit", response_model=APIResponse)
async def submit_quiz(submission: QuizSubmission):
    """
    Submit quiz answers and store rich memory signals:
    topic, score, mistakes, time taken, questions/answers.
    """
    try:
        total = submission.total_questions or len(submission.questions) or 3

        score = submission.score
        if score is None and submission.correct_answers and submission.student_answers:
            pair_count = min(len(submission.correct_answers), len(submission.student_answers))
            score = 0
            for i in range(pair_count):
                student = _normalize_answer(submission.student_answers[i])
                expected = _normalize_answer(submission.correct_answers[i])
                if student and expected and (student == expected or expected in student or student in expected):
                    score += 1
        if score is None:
            score = 0

        mistakes = list(submission.mistakes or [])
        if not mistakes and submission.questions and submission.correct_answers and submission.student_answers:
            pair_count = min(len(submission.questions), len(submission.correct_answers), len(submission.student_answers))
            for i in range(pair_count):
                student = _normalize_answer(submission.student_answers[i])
                expected = _normalize_answer(submission.correct_answers[i])
                if not (student and expected and (student == expected or expected in student or student in expected)):
                    mistakes.append(submission.questions[i])

        score_ratio = max(0.0, min(1.0, float(score) / float(total))) if total else 0.0
        weak_area = mistakes[0] if mistakes else "none"

        content = (
            f"Quiz session on {submission.topic}. "
            f"Score: {score}/{total}. Mistakes: {len(mistakes)}. "
            f"Time taken: {submission.time_taken_seconds or 0}s."
        )
        context = {
            "type": "quiz_session",
            "user_id": submission.user_id,
            "topic": submission.topic,
            "quiz_score": score,
            "quiz_total": total,
            "quiz_score_ratio": round(score_ratio, 3),
            "quiz_mistakes": json.dumps(mistakes),
            "weak_area": weak_area,
            "time_taken_seconds": submission.time_taken_seconds or 0,
            "error_type": "low_quiz_score" if score_ratio < 0.67 else "quiz_mastery",
        }

        memory_status = await hindsight_service.retain_study_session(content=content, context=context)

        return APIResponse(
            status="success",
            data={
                "topic": submission.topic,
                "score": score,
                "total_questions": total,
                "score_ratio": round(score_ratio, 3),
                "mistakes": mistakes,
                "time_taken_seconds": submission.time_taken_seconds or 0,
                "memory_status": memory_status,
            },
            demo_mode=memory_status.get("demo_mode", False),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))