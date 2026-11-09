import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # RESTOCK, SALE_DEDUCT, ADJUSTMENT, SALE_CANCEL_RESTORE
    quantity = Column(Numeric(12, 2), nullable=False)  # Positive for addition, negative for deduction
    reference_id = Column(String(100), nullable=True)  # e.g., sale_id or manual ref
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    business = relationship("Business", back_populates="inventory_transactions")
    product = relationship("Product", back_populates="inventory_transactions")

