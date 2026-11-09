from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)

class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: UUID
    business_id: UUID
    outstanding_balance: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}

class CreditTransactionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class RepaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(default="Cash")
    description: Optional[str] = "Customer repayment"

class CreditTransactionResponse(BaseModel):
    id: UUID
    business_id: UUID
    customer_id: UUID
    sale_id: Optional[UUID] = None
    transaction_type: str  # CREDIT_GIVEN, REPAYMENT
    amount: Decimal
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
