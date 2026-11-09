from uuid import UUID
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

class ExpenseService:
    @staticmethod
    def get_expenses(
        db: Session,
        business_id: UUID,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Expense]:
        query = db.query(Expense).filter(Expense.business_id == business_id)
        if category and category != "All":
            query = query.filter(Expense.category == category)
        return query.order_by(desc(Expense.created_at)).limit(limit).all()

    @staticmethod
    def get_expense_by_id(db: Session, business_id: UUID, expense_id: UUID) -> Expense:
        expense = db.query(Expense).filter(Expense.id == expense_id, Expense.business_id == business_id).first()
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        return expense

    @staticmethod
    def create_expense(db: Session, business_id: UUID, data: ExpenseCreate) -> Expense:
        expense = Expense(
            business_id=business_id,
            category=data.category.strip(),
            description=data.description.strip() if data.description else None,
            amount=data.amount,
            payment_method=data.payment_method
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def update_expense(db: Session, business_id: UUID, expense_id: UUID, data: ExpenseUpdate) -> Expense:
        expense = ExpenseService.get_expense_by_id(db, business_id, expense_id)
        for key, val in data.model_dump(exclude_unset=True).items():
            if val is not None:
                setattr(expense, key, val)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def delete_expense(db: Session, business_id: UUID, expense_id: UUID) -> bool:
        expense = ExpenseService.get_expense_by_id(db, business_id, expense_id)
        db.delete(expense)
        db.commit()
        return True

    @staticmethod
    def get_summary(db: Session, business_id: UUID) -> Dict:
        rows = db.query(
            Expense.category,
            func.coalesce(func.sum(Expense.amount), Decimal("0.00"))
        ).filter(Expense.business_id == business_id).group_by(Expense.category).all()

        breakdown = {cat: amt for cat, amt in rows}
        total = sum(breakdown.values(), Decimal("0.00"))
        return {"total_expenses": total, "category_breakdown": breakdown}
