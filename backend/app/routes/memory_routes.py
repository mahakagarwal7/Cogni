# backend/app/routes/memory_routes.py
from fastapi import APIRouter, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from app.services.hindsight_service import hindsight_service
from app.services.summary_service import summary_service
import io

router = APIRouter(prefix="/memory", tags=["memory"])

# Request models
class SummaryRequest(BaseModel):
    conversation: str

class PDFRequest(BaseModel):
    summary_text: str
    topic_name: str = "learning_summary"

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


@router.post("/summary")
async def generate_conversation_summary(
    request: SummaryRequest
):
    """
    UPGRADE: Generate summary of conversation history.
    
    Handles:
    - Long conversations via chunking
    - Partial summarization per chunk
    - Final summary synthesis
    - Preview extraction for UI
    """
    summary_result = await summary_service.generate_summary(request.conversation)
    
    return {
        "status": "success",
        "data": {
            "preview": summary_result.get("preview", ""),
            "full_summary": summary_result.get("full_summary", ""),
            "demo_mode": summary_result.get("demo_mode", False)
        }
    }


@router.post("/summary/pdf")
async def download_summary_pdf(
    request: PDFRequest
):
    """
    UPGRADE: Download summary as PDF file.
    
    Generates professional PDF report of conversation summary.
    Uses topic name for filename.
    """
    try:
        pdf_bytes = summary_service.generate_pdf(request.summary_text, f"{request.topic_name.replace('_', ' ').title()} - Learning Summary")
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            print("[ERROR] PDF generation returned empty bytes")
            return {
                "status": "error",
                "message": "PDF generation failed - empty output. Try text download instead."
            }
        
        # Return as downloadable PDF
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={request.topic_name}_study_plan.pdf"}
        )
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"PDF generation failed: {str(e)}. Try text download instead."
        }
