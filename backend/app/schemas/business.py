from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class BusinessBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    business_type: str = Field(default="Kirana / Grocery", max_length=100)
    GSTIN: Optional[str] = Field(default=None, max_length=30)
    currency: str = Field(default="INR", max_length=10)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    address: Optional[str] = None

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    GSTIN: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    address: Optional[str] = None

class BusinessResponse(BusinessBase):
    id: UUID
    owner_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
