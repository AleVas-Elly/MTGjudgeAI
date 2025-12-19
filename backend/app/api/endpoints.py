from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

from backend.app.dependencies import get_chat_controller
from backend.app.services.chat_controller import ChatController

router = APIRouter()

# --- Request/Response Models ---
class ChatRequest(BaseModel):
    query: str
    history: List[str] = []
    smart_mode: bool = False
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    context: Dict[str, Any]

class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: str  # "up" (positive) or "down" (negative)
    model: str   # "fast" or "smart"

class ReportRequest(BaseModel):
    query: str
    response: str
    comment: str
    model: str

# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, controller: ChatController = Depends(get_chat_controller)):
    """
    Main chat endpoint.
    Use 'smart_mode=True' to enable the 70B model.
    """
    try:
        result = controller.process_message(
            request.query, 
            request.history, 
            smart_mode=request.smart_mode,
            context=request.context
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def feedback_endpoint(feedback: FeedbackRequest):
    """
    Logs user feedback (thumbs up/down) for RLHF.
    """
    log_file = "logs/feedback.jsonl"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": feedback.query,
        "response": feedback.response,
        "rating": feedback.rating,
        "model": feedback.model
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return {"status": "success"}

@router.post("/report")
async def report_endpoint(report: ReportRequest):
    """
    Logs user bug reports/issues.
    """
    log_file = "logs/issues.jsonl"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": report.query,
        "response": report.response,
        "comment": report.comment,
        "model": report.model
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return {"status": "success"}
