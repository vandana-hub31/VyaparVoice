import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    SKU = Column(String(100), nullable=True, index=True)
    category = Column(String(100), default="General", nullable=False, index=True)
    unit = Column(String(50), default="pcs", nullable=False)  # pcs, kg, g, l, ml, pkt, box
    purchase_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    current_stock = Column(Numeric(12, 2), nullable=False, default=0.0)
    low_stock_threshold = Column(Numeric(12, 2), nullable=False, default=5.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    inventory_transactions = relationship("InventoryTransaction", back_populates="product", cascade="all, delete-orphan")
