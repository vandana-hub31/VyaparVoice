from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class InventoryAdjustment(BaseModel):
    product_id: UUID
    quantity_change: Decimal = Field(..., description="Positive for adding stock, negative for reduction")
    transaction_type: str = Field(default="ADJUSTMENT", description="RESTOCK, ADJUSTMENT, CORRECTION")
    description: Optional[str] = None

class InventoryTransactionResponse(BaseModel):
    id: UUID
    business_id: UUID
    product_id: UUID
    transaction_type: str
    quantity: Decimal
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    product_name: Optional[str] = None

    model_config = {"from_attributes": True}
