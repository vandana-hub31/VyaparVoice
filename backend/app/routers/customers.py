from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CreditTransactionResponse, RepaymentCreate
from app.services.customer_service import CustomerService
from app.utils.dependencies import get_current_business

router = APIRouter(prefix="/api/customers", tags=["Customers"])

@router.get("", response_model=List[CustomerResponse])
def get_customers(
    search: Optional[str] = None,
    has_balance_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return CustomerService.get_customers(
        db, business.id,
        search=search,
        has_balance_only=has_balance_only,
        limit=limit
    )

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return CustomerService.create_customer(db, business.id, data)

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return CustomerService.get_customer_by_id(db, business.id, customer_id)

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return CustomerService.update_customer(db, business.id, customer_id, data)

@router.get("/{customer_id}/ledger", response_model=List[CreditTransactionResponse])
def get_customer_ledger(
    customer_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return CustomerService.get_customer_ledger(db, business.id, customer_id)

@router.post("/{customer_id}/repayments", response_model=CreditTransactionResponse, status_code=status.HTTP_201_CREATED)
def record_customer_repayment(
    customer_id: UUID,
    data: RepaymentCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return CustomerService.record_repayment(db, business.id, customer_id, data)
