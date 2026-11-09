from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class ExpenseBase(BaseModel):
    category: str = Field(default="Miscellaneous", max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(default="Cash", max_length=50)

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    payment_method: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: UUID
    business_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}

class ExpenseSummaryResponse(BaseModel):
    total_expenses: Decimal
    category_breakdown: dict[str, Decimal]
