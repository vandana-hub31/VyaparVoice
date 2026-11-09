from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummaryResponse
from app.services.expense_service import ExpenseService
from app.utils.dependencies import get_current_business

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])

@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ExpenseService.get_expenses(db, business.id, category=category, limit=limit)

@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ExpenseService.create_expense(db, business.id, data)

@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_expense_summary(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ExpenseService.get_summary(db, business.id)

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ExpenseService.get_expense_by_id(db, business.id, expense_id)

@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: UUID,
    data: ExpenseUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ExpenseService.update_expense(db, business.id, expense_id, data)

@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense(
    expense_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    ExpenseService.delete_expense(db, business.id, expense_id)
    return {"status": "success", "message": "Expense deleted successfully"}
