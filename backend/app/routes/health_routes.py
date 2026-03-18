# backend/app/routes/health_routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "cogni-backend",
        "demo_mode": True
    }