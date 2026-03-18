# backend/app/routes/study_routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.engines.archaeology_engine import ArchaeologyEngine
from app.models.memory_types import StudySession, APIResponse

router = APIRouter(prefix="/study", tags=["study"])

# Dependency injection for engine
def get_archaeology_engine():
    return ArchaeologyEngine()

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
    engine: ArchaeologyEngine = Depends(get_archaeology_engine)
):
    """
    GET /api/study/archaeology?topic=recursion&confusion_level=4
    Feature 1: Find when you last felt this confused + what helped.
    """
    if not (1 <= confusion_level <= 5):
        raise HTTPException(status_code=400, detail="confusion_level must be 1-5")
    
    try:
        result = await engine.find_past_struggles(topic, confusion_level, days)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("result", {}).get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))