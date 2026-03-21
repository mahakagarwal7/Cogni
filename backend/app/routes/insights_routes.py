# backend/app/routes/insights_routes.py
from fastapi import APIRouter, HTTPException, Query
from app.engines.shadow_engine import ShadowEngine
from app.engines.resonance_engine import ResonanceEngine
from app.engines.contagion_engine import ContagionEngine
from app.models.memory_types import APIResponse

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/shadow", response_model=APIResponse)
async def get_shadow_prediction(
    topic: str = Query(None, description="Current topic being studied (e.g., recursion)"),
    days: int = Query(7, description="Days to analyze"),
    user_id: str = Query("student", description="User ID for memory tracking")
):
    """Get Cognitive Shadow prediction based on current or past topics"""
    try:
        engine = ShadowEngine()
        result = await engine.get_prediction(current_topic=topic, days=days, user_id=user_id)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns", response_model=APIResponse)
async def get_learning_patterns():
    """Get summarized learning patterns"""
    try:
        engine = ShadowEngine()
        result = await engine.get_learning_patterns()
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resonance", response_model=APIResponse)
async def get_resonance(
    topic: str = Query(..., description="Topic to find connections for"),
    user_id: str = Query("student", description="User ID for memory tracking")
):
    """Find hidden conceptual connections"""
    try:
        engine = ResonanceEngine()
        result = await engine.find_connections(topic, user_id)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contagion", response_model=APIResponse)
async def get_contagion(
    error_pattern: str = Query(..., description="Error pattern to find peer insights"),
    user_id: str = Query("student", description="User ID for memory tracking")
):
    """Get community insights from anonymized peer data"""
    try:
        engine = ContagionEngine()
        result = await engine.get_community_insights(error_pattern, user_id)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))