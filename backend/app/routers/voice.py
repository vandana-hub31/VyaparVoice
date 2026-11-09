from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.business import Business
from app.models.user import User
from app.models.voice import VoiceInteraction
from app.schemas.voice import (
    TranscribeResponse,
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceConfirmRequest,
    VoiceSynthesisRequest,
    VoiceSynthesisResponse
)
from app.services.gnani_service import GnaniService
from app.services.voice_orchestrator import VoiceOrchestrator
from app.utils.dependencies import get_current_business, get_current_user

router = APIRouter(prefix="/api/voice", tags=["Voice Assistant"])

@router.get("/gnani/status")
async def get_gnani_status():
    """Diagnostic check for Gnani API key and connectivity"""
    return await GnaniService.verify_connectivity()

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: str = Form("indic-auto"),
    current_user: User = Depends(get_current_user)
):
    # Validation
    if not file.content_type.startswith("audio/") and not file.filename.endswith(('.wav', '.mp3', '.ogg', '.m4a', '.webm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid audio file"
        )

    audio_bytes = await file.read()
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25 MB max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file exceeds 25 MB size limit"
        )

    res = await GnaniService.transcribe_audio(
        audio_bytes=audio_bytes,
        filename=file.filename or "recording.wav",
        language_code=language
    )

    if res.get("error") and not res.get("transcription"):
        # If API key is not configured or failed, report clearly
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY if "401" not in res.get("error", "") else status.HTTP_401_UNAUTHORIZED,
            detail=res.get("error")
        )

    return TranscribeResponse(
        transcription=res.get("transcription", ""),
        detected_language=res.get("detected_language", "en-IN"),
        confidence=res.get("confidence", 0.95)
    )

@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    request: VoiceCommandRequest,
    business: Business = Depends(get_current_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not request.transcription or not request.transcription.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcription cannot be empty")

    return await VoiceOrchestrator.process_command(
        db=db,
        business=business,
        user=current_user,
        transcription=request.transcription.strip(),
        lang=request.language or "auto",
        idempotency_key=request.idempotency_key
    )

@router.post("/confirm", response_model=VoiceCommandResponse)
async def confirm_voice_action(
    request: VoiceConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await VoiceOrchestrator.confirm_action(
        db=db,
        token=request.confirmation_token,
        confirmed=request.confirmed,
        current_user_id=current_user.id
    )

@router.post("/synthesize", response_model=VoiceSynthesisResponse)
async def synthesize_speech(
    request: VoiceSynthesisRequest,
    current_user: User = Depends(get_current_user)
):
    audio_b64 = await GnaniService.synthesize_speech(
        text=request.text,
        language=request.language or "en-IN",
        voice=request.voice or "Shivani",
        speed=request.speed or 1.0
    )
    if not audio_b64:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Speech synthesis failed or API key missing")
    return VoiceSynthesisResponse(audio_base64=audio_b64, mime_type="audio/wav")

@router.get("/history")
def get_voice_history(
    limit: int = 20,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    interactions = db.query(VoiceInteraction)\
        .filter(VoiceInteraction.business_id == business.id)\
        .order_by(desc(VoiceInteraction.created_at))\
        .limit(limit)\
        .all()
    return [
        {
            "id": str(i.id),
            "transcription": i.transcription,
            "detected_intent": i.detected_intent,
            "execution_status": i.execution_status,
            "response_text": i.response_text,
            "input_language": i.input_language,
            "created_at": i.created_at.isoformat()
        } for i in interactions
    ]


