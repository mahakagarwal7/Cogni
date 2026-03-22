# backend/app/routes/socratic_routes.py
from fastapi import APIRouter, HTTPException, Query
from app.engines.socratic_engine import SocraticEngine
from app.models.memory_types import Misconception, APIResponse
from app.services.prompt_template_service import prompt_template_service
from typing import Optional

router = APIRouter(prefix="/socratic", tags=["socratic"])

@router.post("/ask", response_model=APIResponse)
async def ask_question(
    concept: str,
    user_belief: str,
    confusion_level: int = Query(3, ge=1, le=5, description="Confusion level from 1 (clear) to 5 (very confused)"),
    user_id: str = Query("student", description="User ID for personalization")
):
    """Ask a Socratic question based on past misconceptions with adaptive tutoring"""
    try:
        engine = SocraticEngine()
        result = await engine.ask_socratic_question(concept, user_belief, user_id, confusion_level)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reflect", response_model=APIResponse)
async def reflect_on_response(
    concept: str,
    user_response: str,
    previous_question: str,
    confusion_level: int = Query(3, ge=1, le=5, description="Confusion level from 1 (clear) to 5 (very confused)"),
    user_id: str = Query("student", description="User ID for personalization")
):
    """Reflect on user response and generate adaptive follow-up question.
    
    This is the core Hindsight feedback loop:
    1. Retain: User response is saved to memory
    2. Recall: Previous interactions are retrieved
    3. Reflect: Better follow-up question is generated based on response
    """
    try:
        engine = SocraticEngine()
        result = await engine.reflect_on_response(
            concept=concept,
            user_response=user_response,
            user_id=user_id,
            previous_question=previous_question,
            confusion_level=confusion_level
        )
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hint", response_model=APIResponse)
async def get_socratic_hint(
    concept: str,
    previous_question: str,
    user_response: str = Query("", description="Optional latest user response for hint personalization"),
    confusion_level: int = Query(3, ge=1, le=5, description="Confusion level from 1 (clear) to 5 (very confused)"),
    user_id: str = Query("student", description="User ID for personalization")
):
    """Return a micro-hint for the current Socratic step with minimal overhead."""
    try:
        engine = SocraticEngine()
        result = await engine.get_hint(
            concept=concept,
            previous_question=previous_question,
            user_id=user_id,
            confusion_level=confusion_level,
            user_response=user_response,
        )
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log", response_model=APIResponse)
async def log_misconception(misconception: Misconception):
    """Save a misconception to memory"""
    try:
        engine = SocraticEngine()
        result = await engine.log_misconception(misconception)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=APIResponse)
async def get_history(concept: str):
    """Get dialogue history for a concept"""
    try:
        engine = SocraticEngine()
        result = await engine.get_dialogue_history(concept)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/killer-prompt-preview", response_model=APIResponse)
async def preview_killer_prompt(
    user_id: str = Query(..., description="User ID"),
    query: str = Query(..., description="Student query or concept"),
    topic: Optional[str] = Query(None, description="Optional topic for context")
):
    """
    PHASE 9 Preview: Show the killer prompt that will be used for personalized tutoring.
    Returns the memory context and full adaptive prompt.
    """
    try:
        # Build memory context
        memory_context = await prompt_template_service.build_memory_context(user_id, query, topic)
        
        # Build killer prompt
        killer_prompt = prompt_template_service.build_killer_prompt(user_id, memory_context, query)
        
        # Extract adaptive rules
        rules = prompt_template_service.extract_adaptive_rules_from_context(memory_context)
        
        return APIResponse(
            status="success",
            data={
                "orchestrator_stage": "killer_prompt_preview",
                "user_id": user_id,
                "query": query,
                "topic": topic,
                "memory_context": memory_context,
                "killer_prompt": killer_prompt,
                "adaptive_rules": rules,
            },
            demo_mode=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))