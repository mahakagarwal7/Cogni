# backend/app/models/memory_types.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime

class StudySession(BaseModel):
    """
    📝 Data Contract for Study Sessions.
    ALL features must use this schema when saving to memory.
    """
    topic: str = Field(..., description="Subject being studied")
    confusion_level: int = Field(..., ge=1, le=5, description="1-5 confusion scale")
    error_pattern: str = Field(..., description="e.g., 'base_case_missing'")
    hint_used: Optional[str] = Field(None, description="What hint was tried")
    outcome: Literal["resolved", "partial", "unresolved"] = Field(...)
    time_spent_seconds: Optional[int] = Field(None)
    emotional_cue: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "recursion",
                "confusion_level": 4,
                "error_pattern": "base_case_missing",
                "hint_used": "visual_gift_analogy",
                "outcome": "resolved",
                "time_spent_seconds": 420
            }
        }


class Misconception(BaseModel):
    """
    📝 Data Contract for Misconceptions (Socratic Ghost).
    """
    concept: str = Field(..., description="The concept misunderstood")
    incorrect_belief: str = Field(..., description="What they thought was true")
    question_asked: str = Field(..., description="Socratic question asked")
    user_response: str = Field(..., description="How they responded")
    resolved: bool = Field(..., description="Was it resolved?")
    related_sessions: Optional[List[str]] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "concept": "recursion",
                "incorrect_belief": "recursion is just loops",
                "question_asked": "What happens to the call stack?",
                "user_response": "It grows",
                "resolved": True
            }
        }


class MemoryContent(BaseModel):
    """
    📝 Unified schema for Hindsight retain() calls.
    """
    content: str
    content_type: Literal["StudySession", "Misconception", "Observation"]
    context: dict
    tags: Optional[List[str]] = None
    timestamp: str


class APIResponse(BaseModel):
    """
    📝 Standard API response wrapper.
    """
    status: Literal["success", "error"]
    data: Optional[dict] = None
    message: Optional[str] = None
    demo_mode: bool = False


class InteractionRecord(BaseModel):
    """
    Structured interaction schema for orchestration memory.
    """
    interaction_id: str = Field(..., description="Unique interaction id")
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="User query text")
    response: str = Field(..., description="Assistant response text")
    engine_used: str = Field(..., description="Engine selected by orchestrator")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRecord(BaseModel):
    """
    Structured feedback schema linked to one interaction.
    """
    interaction_id: str = Field(..., description="Linked interaction id")
    understood: bool = Field(..., description="Whether user understood the response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="User confidence score")
    feedback_text: str = Field(..., description="Raw user feedback text")


class InsightRecord(BaseModel):
    """
    Structured insight schema stored in memory for future improvements.
    """
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Topic associated with the issue")
    issue: str = Field(..., description="Core issue inferred from feedback")
    preferred_style: str = Field(..., description="Preferred explanation style")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Insight confidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizQuestion(BaseModel):
    id: int = Field(..., ge=1, description="Question index")
    question: str = Field(..., description="Quiz question text")
    expected_answer: str = Field(..., description="Reference answer")
    options: Optional[List[str]] = Field(default=None, description="Optional multiple-choice options")


class QuizSubmission(BaseModel):
    user_id: str = Field("student", description="User identifier")
    topic: str = Field(..., description="Quiz topic")
    questions: List[str] = Field(default_factory=list)
    student_answers: List[str] = Field(default_factory=list)
    correct_answers: List[str] = Field(default_factory=list)
    score: Optional[int] = Field(None, ge=0, description="Correct answers count")
    total_questions: Optional[int] = Field(None, ge=1)
    mistakes: Optional[List[str]] = Field(default_factory=list)
    time_taken_seconds: Optional[int] = Field(None, ge=0)