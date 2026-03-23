# backend/app/routes/study_routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Any
from app.engines.archaeology_engine import ArchaeologyEngine
from app.models.memory_types import StudySession, APIResponse, QuizSubmission
from app.services.hindsight_service import hindsight_service
from app.services.llm_service import llm_service
import json
import re
import random

router = APIRouter(prefix="/study", tags=["study"])

# Dependency injection for engine
def get_archaeology_engine():
    return ArchaeologyEngine()


def _tokenize_for_similarity(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(text or "").lower())
    return {tok for tok in cleaned.split() if len(tok) > 2}


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    a = _tokenize_for_similarity(text_a)
    b = _tokenize_for_similarity(text_b)
    if not a or not b:
        return 0.0
    return len(a.intersection(b)) / float(max(1, len(a.union(b))))


def _is_question_topic_aligned(question: str, topic: str) -> bool:
    q = str(question or "").strip().lower()
    t = str(topic or "").strip().lower()
    if not q or not t:
        return False

    topic_tokens = [tok for tok in re.sub(r"[^a-z0-9\s]", " ", t).split() if len(tok) > 2]
    if not topic_tokens:
        return t in q

    overlap = sum(1 for tok in topic_tokens if tok in q)
    return overlap >= 1


def _has_low_option_diversity(options: list[str], expected_answer: str) -> bool:
    cleaned = [str(opt).strip() for opt in (options or []) if str(opt).strip()]
    if len(cleaned) < 4:
        return True

    normalized = [opt.lower() for opt in cleaned]
    if len(set(normalized)) < 4:
        return True

    expected_lower = str(expected_answer or "").strip().lower()
    distractors = [opt for opt in cleaned if opt.lower() != expected_lower]
    if len(distractors) < 3:
        return True

    for i in range(len(distractors)):
        for j in range(i + 1, len(distractors)):
            if _jaccard_similarity(distractors[i], distractors[j]) >= 0.68:
                return True

    opening_phrases = [" ".join(d.lower().split()[:4]) for d in distractors if len(d.split()) >= 4]
    if len(opening_phrases) != len(set(opening_phrases)):
        return True

    return False


def _extract_weak_topics_from_evidence(evidence: list[str]) -> list[str]:
    weak_topics: list[str] = []
    for item in evidence or []:
        text = str(item or "").strip()
        if "quiz weakness detected in:" not in text.lower():
            continue
        rhs = text.split(":", 1)[1] if ":" in text else ""
        for topic in rhs.split(","):
            clean = topic.strip()
            if clean and clean.lower() not in {w.lower() for w in weak_topics}:
                weak_topics.append(clean)
    return weak_topics


async def _build_quiz_hindsight_context(topic: str, user_id: str) -> dict[str, Any]:
    context: dict[str, Any] = {
        "prediction": "",
        "evidence": [],
        "weak_topics": [],
        "recent_topics": [],
    }

    try:
        shadow = await hindsight_service.reflect_cognitive_shadow(
            days=60,
            user_id=user_id,
            current_topic=topic,
        )
        evidence = shadow.get("evidence") if isinstance(shadow, dict) else []
        recent_topics = shadow.get("recent_topics") if isinstance(shadow, dict) else []
        prediction = str((shadow or {}).get("prediction", "")).strip() if isinstance(shadow, dict) else ""
        context["prediction"] = prediction
        context["evidence"] = [str(x).strip() for x in evidence if str(x).strip()]
        context["recent_topics"] = [str(x).strip() for x in recent_topics if str(x).strip()]
        context["weak_topics"] = _extract_weak_topics_from_evidence(context["evidence"])
    except Exception:
        pass

    return context


def _build_quiz_prompt(topic: str, hindsight_context: dict[str, Any]) -> str:
    weak_topics = hindsight_context.get("weak_topics") or []
    prediction = str(hindsight_context.get("prediction") or "").strip()
    evidence = hindsight_context.get("evidence") or []

    weakness_line = ", ".join(weak_topics[:3]) if weak_topics else "none"
    evidence_line = "; ".join([str(item) for item in evidence[:2]]) if evidence else "none"

    return f"""Generate exactly 3 multiple-choice revision questions for topic: {topic}.
Personalize using hindsight signals when relevant.

Hindsight weak areas: {weakness_line}
Hindsight prediction: {prediction or 'none'}
Hindsight evidence: {evidence_line}

Return JSON array only in this format:
[
    {{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}},
    {{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}},
    {{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}}
]

Hard rules:
- Exactly 3 questions and exactly 4 options per question.
- Every question must explicitly mention '{topic}' or a direct topic term.
- expected_answer must match one option exactly.
- Options must be materially different in meaning and wording (no one-word swaps).
- Three distractors must each represent different error modes:
  1) overgeneralization,
  2) missing condition/step,
  3) confusion with a related concept.
- Avoid generic options like 'I don't know' or 'Need more context'.
- Keep options concise.
- No extra text outside JSON."""


def _extract_json_array(raw: str) -> list[Any]:
    cleaned = str(raw or "").replace("<think>", "").replace("</think>", "").strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    try:
        parsed = json.loads(cleaned[start:end + 1])
    except Exception:
        return []

    return parsed if isinstance(parsed, list) else []


def _build_quiz_repair_prompt(topic: str, previous_output: str) -> str:
    return f"""Rewrite the following output into valid JSON ONLY.

Topic: {topic}
Bad output:
{previous_output}

Required format:
[
  {{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}},
  {{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}},
  {{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}}
]

Rules:
- Exactly 3 questions.
- Exactly 4 options each.
- expected_answer appears exactly once in options.
- Every question must be explicitly about {topic}.
- Return only JSON array, no markdown.
"""


def _build_llm_options(question: str, expected_answer: str, topic: str, hindsight_context: dict[str, Any]) -> list[str]:
    expected = str(expected_answer).strip()
    weak_topics = hindsight_context.get("weak_topics") or []
    weakness_line = ", ".join(weak_topics[:2]) if weak_topics else "none"

    prompt = f"""For this MCQ, generate 4 options as a JSON array of strings.

Topic: {topic}
Question: {question}
Correct answer (must appear exactly once): {expected}
Relevant weak areas: {weakness_line}

Rules:
- Return only a JSON array with exactly 4 strings.
- Include the correct answer exactly once.
- Create 3 distractors that are plausible but clearly different from each other in logic and wording.
- Do not use templated openings repeated across distractors.
- Keep each option concise.
"""

    raw = llm_service.generate(prompt, max_tokens=220, temperature=0.85)
    cleaned = str(raw or "").replace("<think>", "").replace("</think>", "").strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    try:
        parsed = json.loads(cleaned[start:end + 1])
    except Exception:
        return []

    if not isinstance(parsed, list):
        return []

    normalized: list[str] = []
    seen = set()
    for item in parsed:
        opt = str(item).strip()
        if not opt:
            continue
        low = opt.lower()
        if low in seen:
            continue
        seen.add(low)
        normalized.append(opt)

    if all(opt.lower() != expected.lower() for opt in normalized):
        if len(normalized) >= 4:
            normalized[-1] = expected
        else:
            normalized.append(expected)

    if len(normalized) >= 4:
        random.shuffle(normalized)
        return normalized[:4]

    return []


def _build_single_llm_question(topic: str, hindsight_context: dict[str, Any]) -> dict[str, Any]:
    weak_topics = hindsight_context.get("weak_topics") or []
    weakness_line = ", ".join(weak_topics[:2]) if weak_topics else "none"
    prompt = f"""Generate one multiple-choice question about topic: {topic}.

Use this exact JSON object format only:
{{"question":"...", "expected_answer":"...", "options":["...","...","...","..."]}}

Rules:
- Question must explicitly mention {topic}.
- Exactly 4 options.
- expected_answer must appear exactly once in options.
- Distractors must be plausible and mutually different.
- Consider this weakness context if useful: {weakness_line}
- Return only JSON object.
"""

    raw = llm_service.generate(prompt, max_tokens=260, temperature=0.85)
    cleaned = str(raw or "").replace("<think>", "").replace("</think>", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        parsed = json.loads(cleaned[start:end + 1])
    except Exception:
        return {}

    if not isinstance(parsed, dict):
        return {}

    q = str(parsed.get("question", "")).strip()
    a = str(parsed.get("expected_answer", "")).strip()
    options_raw = parsed.get("options")
    options = [str(opt).strip() for opt in options_raw] if isinstance(options_raw, list) else []

    if not q or not a or not _is_question_topic_aligned(q, topic):
        return {}

    if not options or _has_low_option_diversity(options, a):
        options = _build_llm_options(q, a, topic, hindsight_context) or _build_topic_options(q, a, topic)

    return {"question": q, "expected_answer": a, "options": options[:4]}


def _post_process_quiz_rows(rows: list[dict], topic: str, hindsight_context: dict[str, Any]) -> list[dict]:
    questions: list[dict] = []
    for idx, row in enumerate(rows[:3], start=1):
        if not isinstance(row, dict):
            continue
        question = str(row.get("question", "")).strip()
        expected = str(row.get("expected_answer", "")).strip()
        options_raw = row.get("options")
        options = [str(opt).strip() for opt in options_raw] if isinstance(options_raw, list) else []

        if not question or not expected or not _is_question_topic_aligned(question, topic):
            continue

        if not options or _has_low_option_diversity(options, expected):
            regenerated = _build_llm_options(question, expected, topic, hindsight_context)
            options = regenerated if regenerated else _build_topic_options(question, expected, topic)

        questions.append({"id": idx, "question": question, "expected_answer": expected, "options": options[:4]})

    while len(questions) < 3 and llm_service.available:
        generated = _build_single_llm_question(topic, hindsight_context)
        if not generated:
            break
        next_id = len(questions) + 1
        questions.append({
            "id": next_id,
            "question": generated["question"],
            "expected_answer": generated["expected_answer"],
            "options": generated["options"],
        })

    if len(questions) < 3:
        fallback_rows = _fallback_quiz(topic)
        for row in fallback_rows:
            if len(questions) >= 3:
                break
            if any(q["question"].lower() == str(row.get("question", "")).strip().lower() for q in questions):
                continue
            questions.append({
                "id": len(questions) + 1,
                "question": str(row.get("question", "")).strip(),
                "expected_answer": str(row.get("expected_answer", "")).strip(),
                "options": [str(opt).strip() for opt in (row.get("options") or [])][:4],
            })

    return questions[:3]


def _fallback_quiz(topic: str) -> list[dict]:
    rows = [
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

    for row in rows:
        row["options"] = _build_topic_options(
            question=str(row["question"]),
            expected_answer=str(row["expected_answer"]),
            topic=topic,
        )
    return rows


def _build_topic_options(question: str, expected_answer: str, topic: str) -> list[str]:
    """Create 4 MCQ options: 1 correct + 3 topic-relevant distractors."""
    expected = str(expected_answer).strip()
    base_distractors = [
        f"A broad statement about {topic} that overgeneralizes and fails on edge cases.",
        f"An explanation of {topic} that skips a required condition or intermediate step.",
        f"A description that confuses {topic} with a nearby but distinct concept.",
    ]

    # Keep distractors unique and not equal to expected.
    seen = {expected.lower()}
    distractors: list[str] = []
    for d in base_distractors:
        d_clean = d.strip()
        if not d_clean:
            continue
        lowered = d_clean.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        distractors.append(d_clean)

    options = [expected] + distractors[:3]
    random.shuffle(options)
    return options[:4]


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
        options_raw = row.get("options")
        options = [str(opt).strip() for opt in options_raw] if isinstance(options_raw, list) else []

        if q and a and _is_question_topic_aligned(q, topic):
            if not options:
                options = _build_topic_options(q, a, topic)
            else:
                # Ensure answer appears once and keep topic-relevant options.
                normalized = []
                seen = set()
                for opt in options:
                    if not opt:
                        continue
                    low = opt.lower()
                    if low in seen:
                        continue
                    seen.add(low)
                    normalized.append(opt)
                options = normalized[:4]
                if all(a.lower() != opt.lower() for opt in options):
                    if len(options) >= 4:
                        options[-1] = a
                    else:
                        options.append(a)
                if len(options) < 4:
                    extra = _build_topic_options(q, a, topic)
                    for opt in extra:
                        if len(options) >= 4:
                            break
                        if opt.lower() not in {x.lower() for x in options}:
                            options.append(opt)
                random.shuffle(options)

            questions.append({"id": idx, "question": q, "expected_answer": a, "options": options[:4]})

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
            hindsight_context = await _build_quiz_hindsight_context(topic=topic, user_id=user_id)
            prompt = _build_quiz_prompt(topic=topic, hindsight_context=hindsight_context)
            raw = llm_service.generate(prompt, max_tokens=650, temperature=0.8)
            initial_rows = _extract_json_array(raw)
            if not initial_rows:
                repair_prompt = _build_quiz_repair_prompt(topic=topic, previous_output=raw)
                repaired_raw = llm_service.generate(repair_prompt, max_tokens=650, temperature=0.2)
                initial_rows = _extract_json_array(repaired_raw)

            if not initial_rows:
                parsed_rows = _safe_parse_quiz_json(raw, topic)
                initial_rows = [
                    {
                        "question": q.get("question", ""),
                        "expected_answer": q.get("expected_answer", ""),
                        "options": q.get("options", []),
                    }
                    for q in parsed_rows
                ]

            questions = _post_process_quiz_rows(initial_rows, topic, hindsight_context)
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
            "quiz_questions": json.dumps(submission.questions or []),
            "quiz_correct_answers": json.dumps(submission.correct_answers or []),
            "quiz_student_answers": json.dumps(submission.student_answers or []),
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