from pydantic import BaseModel
from typing import List
from datetime import datetime

class APIRequest(BaseModel):
    message: str
    conversation_id: str
    sender_id: str
    message_id: str

class APIResponse(BaseModel):
    response: str
    conversation_id: str
    scam_detected: bool
    timestamp: datetime