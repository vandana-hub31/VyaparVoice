from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    SKU: Optional[str] = Field(default=None, max_length=100)
    category: str = Field(default="General", max_length=100)
    unit: str = Field(default="pcs", max_length=50)  # pcs, kg, g, l, ml, pkt, box
    purchase_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    selling_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    current_stock: Decimal = Field(default=Decimal("0.00"), ge=0)
    low_stock_threshold: Decimal = Field(default=Decimal("5.00"), ge=0)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    SKU: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    purchase_price: Optional[Decimal] = Field(default=None, ge=0)
    selling_price: Optional[Decimal] = Field(default=None, ge=0)
    current_stock: Optional[Decimal] = Field(default=None, ge=0)
    low_stock_threshold: Optional[Decimal] = Field(default=None, ge=0)

class ProductResponse(ProductBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
