from fastapi import APIRouter
from datetime import datetime
from app.models import APIRequest, APIResponse
from app.agents.scam_detector import ScamDetector

router = APIRouter()
detector = ScamDetector()

@router.post("/process")
async def process_message(request: APIRequest):
    # Detect scam
    detection = detector.detect(request.message)
    
    # Simple response logic
    if detection["is_scam"]:
        response_text = f"I see. Can you provide more details? (Score: {detection['score']})"
    else:
        response_text = "Hello, can you tell me more about this?"
    
    return APIResponse(
        response=response_text,
        conversation_id=request.conversation_id,
        scam_detected=detection["is_scam"],
        timestamp=datetime.now()
    )