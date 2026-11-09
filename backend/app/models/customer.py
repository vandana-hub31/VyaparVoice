import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True, index=True)
    address = Column(Text, nullable=True)
    outstanding_balance = Column(Numeric(12, 2), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="customers")
    sales = relationship("Sale", back_populates="customer")
    credit_transactions = relationship("CreditTransaction", back_populates="customer", cascade="all, delete-orphan")

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(String(50), nullable=False)  # CREDIT_GIVEN, REPAYMENT
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    business = relationship("Business", back_populates="credit_transactions")
    customer = relationship("Customer", back_populates="credit_transactions")
    sale = relationship("Sale", back_populates="credit_transactions")

