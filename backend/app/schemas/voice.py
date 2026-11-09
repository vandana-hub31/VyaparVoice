from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.schemas.intent import ParsedIntent

class TranscribeResponse(BaseModel):
    transcription: str
    detected_language: str
    confidence: float
    duration_seconds: Optional[float] = None

class VoiceCommandRequest(BaseModel):
    transcription: Optional[str] = None
    language: Optional[str] = "auto"
    idempotency_key: Optional[str] = None

class ActionConfirmationDetails(BaseModel):
    action_type: str
    summary: str
    params: Dict[str, Any]
    expires_at: datetime

class VoiceCommandResponse(BaseModel):
    interaction_id: Optional[UUID] = None
    transcription: str
    detected_language: str
    parsed_intent: ParsedIntent
    execution_status: str  # SUCCESS, PENDING_CONFIRMATION, FAILED, CLARIFICATION_NEEDED
    response_text: str
    audio_base64: Optional[str] = None
    confirmation_token: Optional[str] = None
    pending_action: Optional[ActionConfirmationDetails] = None
    data: Optional[Dict[str, Any]] = None

class VoiceConfirmRequest(BaseModel):
    confirmation_token: str
    confirmed: bool  # True to execute, False to cancel

class VoiceSynthesisRequest(BaseModel):
    text: str
    language: Optional[str] = "en-IN"
    voice: Optional[str] = "Shivani"
    speed: Optional[float] = 1.0

class VoiceSynthesisResponse(BaseModel):
    audio_base64: str
    mime_type: str = "audio/wav"


