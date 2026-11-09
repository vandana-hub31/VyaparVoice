import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100), default="Kirana / Grocery", nullable=False)
    GSTIN = Column(String(30), nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="businesses")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="business", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="business", cascade="all, delete-orphan")
    inventory_transactions = relationship("InventoryTransaction", back_populates="business", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="business", cascade="all, delete-orphan")
    voice_interactions = relationship("VoiceInteraction", back_populates="business", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="business", cascade="all, delete-orphan")
