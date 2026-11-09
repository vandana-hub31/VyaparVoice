import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class VoiceInteraction(Base):
    __tablename__ = "voice_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    input_language = Column(String(20), default="auto", nullable=False)
    transcription = Column(Text, nullable=False)
    detected_intent = Column(String(100), nullable=False)
    execution_status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, PENDING_CONFIRMATION, FAILED, CANCELLED
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    business = relationship("Business", back_populates="voice_interactions")
    user = relationship("User", back_populates="voice_interactions")
