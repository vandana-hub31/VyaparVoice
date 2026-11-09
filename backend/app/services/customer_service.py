from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException, status

from app.models.customer import Customer, CreditTransaction
from app.schemas.customer import CustomerCreate, CustomerUpdate, RepaymentCreate

class CustomerService:
    @staticmethod
    def get_customers(
        db: Session,
        business_id: UUID,
        search: Optional[str] = None,
        has_balance_only: bool = False,
        limit: int = 100
    ) -> List[Customer]:
        query = db.query(Customer).filter(Customer.business_id == business_id)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(or_(Customer.customer_name.ilike(search_term), Customer.phone.ilike(search_term)))
        if has_balance_only:
            query = query.filter(Customer.outstanding_balance > 0)
        return query.order_by(Customer.customer_name.asc()).limit(limit).all()

    @staticmethod
    def get_customer_by_id(db: Session, business_id: UUID, customer_id: UUID) -> Customer:
        customer = db.query(Customer).filter(Customer.id == customer_id, Customer.business_id == business_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    @staticmethod
    def get_customer_by_name(db: Session, business_id: UUID, name: str) -> Optional[Customer]:
        return db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.customer_name.ilike(name.strip())
        ).first()

    @staticmethod
    def create_customer(db: Session, business_id: UUID, data: CustomerCreate) -> Customer:
        customer = Customer(
            business_id=business_id,
            customer_name=data.customer_name.strip(),
            phone=data.phone.strip() if data.phone else None,
            address=data.address.strip() if data.address else None,
            outstanding_balance=data.initial_balance
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        if data.initial_balance > 0:
            tx = CreditTransaction(
                business_id=business_id,
                customer_id=customer.id,
                transaction_type="CREDIT_GIVEN",
                amount=data.initial_balance,
                description="Opening credit balance"
            )
            db.add(tx)
            db.commit()

        return customer

    @staticmethod
    def update_customer(db: Session, business_id: UUID, customer_id: UUID, data: CustomerUpdate) -> Customer:
        customer = CustomerService.get_customer_by_id(db, business_id, customer_id)
        for key, val in data.model_dump(exclude_unset=True).items():
            if val is not None:
                setattr(customer, key, val)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_customer_ledger(db: Session, business_id: UUID, customer_id: UUID) -> List[CreditTransaction]:
        CustomerService.get_customer_by_id(db, business_id, customer_id)
        return db.query(CreditTransaction)\
            .filter(CreditTransaction.customer_id == customer_id, CreditTransaction.business_id == business_id)\
            .order_by(desc(CreditTransaction.created_at))\
            .all()

    @staticmethod
    def record_repayment(db: Session, business_id: UUID, customer_id: UUID, data: RepaymentCreate) -> CreditTransaction:
        customer = CustomerService.get_customer_by_id(db, business_id, customer_id)
        
        # Deduct from outstanding balance
        customer.outstanding_balance = max(Decimal("0.00"), customer.outstanding_balance - data.amount)
        
        tx = CreditTransaction(
            business_id=business_id,
            customer_id=customer.id,
            transaction_type="REPAYMENT",
            amount=data.amount,
            description=f"{data.description} ({data.payment_method})"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
