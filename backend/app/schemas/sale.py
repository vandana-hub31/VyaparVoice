from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class SaleItemCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(..., gt=0)
    # Unit price is optional from frontend; backend looks up actual selling_price unless explicitly overridden
    unit_price: Optional[Decimal] = None

class SaleCreate(BaseModel):
    items: List[SaleItemCreate] = Field(..., min_length=1)
    customer_id: Optional[UUID] = None
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_rate_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    payment_method: str = Field(default="Cash", description="Cash, UPI, Card, Credit")
    idempotency_key: Optional[str] = None

class SaleItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    purchase_price_snapshot: Decimal
    total_amount: Decimal

    model_config = {"from_attributes": True}

class SaleResponse(BaseModel):
    id: UUID
    business_id: UUID
    customer_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    invoice_number: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal
    payment_method: str
    payment_status: str
    created_at: datetime
    items_count: Optional[int] = 0

    model_config = {"from_attributes": True}

class SaleDetailResponse(SaleResponse):
    items: List[SaleItemResponse]
