# backend/app/routes/memory_routes.py
from fastapi import APIRouter, Query
from app.services.hindsight_service import hindsight_service

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/recall")
async def recall_memories(
    query: str = Query("*", description="Search query"),
    limit: int = Query(10, description="Max results")
):
    """Memory Inspector: Get memories for transparency"""
    memories = await hindsight_service.recall_all_memories(limit=limit)
    return {
        "status": "success",
        "count": len(memories),
        "memories": memories,
        "demo_mode": True  # Will be false if real API works
    }