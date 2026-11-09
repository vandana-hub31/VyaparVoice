import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # Rent, Electricity, Transport, Salaries, Inventory Purchase, Miscellaneous
    description = Column(String(255), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), default="Cash", nullable=False)  # Cash, UPI, Bank Transfer
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    business = relationship("Business", back_populates="expenses")

