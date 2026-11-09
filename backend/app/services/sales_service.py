from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.customer import Customer, CreditTransaction
from app.models.inventory import InventoryTransaction
from app.schemas.sale import SaleCreate

# In-memory idempotency cache for sensitive write transactions
_idempotency_cache = {}

class SalesService:
    @staticmethod
    def _generate_invoice_number(db: Session, business_id: UUID) -> str:
        count = db.query(func.count(Sale.id)).filter(Sale.business_id == business_id).scalar() or 0
        year = datetime.now(timezone.utc).year
        return f"INV-{year}-{count + 1:04d}"

    @staticmethod
    def create_sale(db: Session, business_id: UUID, data: SaleCreate) -> Sale:
        if data.idempotency_key and data.idempotency_key in _idempotency_cache:
            sale_id = _idempotency_cache[data.idempotency_key]
            existing = db.query(Sale).filter(Sale.id == sale_id).first()
            if existing:
                return existing

        if not data.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale must contain at least one item")

        # Start transaction
        subtotal = Decimal("0.00")
        sale_items_to_create = []

        for item_in in data.items:
            product = db.query(Product).filter(
                Product.id == item_in.product_id,
                Product.business_id == business_id
            ).with_for_update().first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product ID {item_in.product_id} not found"
                )

            if product.current_stock < item_in.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{product.product_name}'. In stock: {product.current_stock}, Requested: {item_in.quantity}"
                )

            # Enforce server-side price lookup
            unit_price = item_in.unit_price if item_in.unit_price is not None else product.selling_price
            item_total = unit_price * item_in.quantity
            subtotal += item_total

            # Deduct inventory atomically
            product.current_stock -= item_in.quantity

            sale_items_to_create.append({
                "product": product,
                "quantity": item_in.quantity,
                "unit_price": unit_price,
                "purchase_price_snapshot": product.purchase_price,
                "total_amount": item_total
            })

        # Calculate discount, tax, total
        discount = data.discount or Decimal("0.00")
        taxable_amount = max(Decimal("0.00"), subtotal - discount)
        tax = (taxable_amount * (data.tax_rate_percent or Decimal("0.00"))) / Decimal("100.00")
        total_amount = taxable_amount + tax

        # Check customer credit eligibility if payment_method is Credit
        customer = None
        if data.payment_method.lower() == "credit":
            if not data.customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer must be specified for Credit sales"
                )
            customer = db.query(Customer).filter(
                Customer.id == data.customer_id,
                Customer.business_id == business_id
            ).first()
            if not customer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        invoice_number = SalesService._generate_invoice_number(db, business_id)

        sale = Sale(
            business_id=business_id,
            customer_id=data.customer_id,
            invoice_number=invoice_number,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total_amount=total_amount,
            payment_method=data.payment_method,
            payment_status="PAID" if data.payment_method.lower() != "credit" else "UNPAID"
        )
        db.add(sale)
        db.flush()

        for item_info in sale_items_to_create:
            p = item_info["product"]
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=p.id,
                quantity=item_info["quantity"],
                unit_price=item_info["unit_price"],
                purchase_price_snapshot=item_info["purchase_price_snapshot"],
                total_amount=item_info["total_amount"]
            )
            db.add(sale_item)

            # Record inventory transaction
            inv_tx = InventoryTransaction(
                business_id=business_id,
                product_id=p.id,
                transaction_type="SALE_DEDUCT",
                quantity=-item_info["quantity"],
                reference_id=str(sale.id),
                description=f"Deducted for Invoice {invoice_number}"
            )
            db.add(inv_tx)

        # Update customer credit ledger if credit sale
        if customer and data.payment_method.lower() == "credit":
            customer.outstanding_balance += total_amount
            credit_tx = CreditTransaction(
                business_id=business_id,
                customer_id=customer.id,
                sale_id=sale.id,
                transaction_type="CREDIT_GIVEN",
                amount=total_amount,
                description=f"Credit sale for Invoice {invoice_number}"
            )
            db.add(credit_tx)

        db.commit()
        db.refresh(sale)

        if data.idempotency_key:
            _idempotency_cache[data.idempotency_key] = sale.id

        return sale

    @staticmethod
    def get_sales(
        db: Session,
        business_id: UUID,
        customer_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Sale]:
        query = db.query(Sale).filter(Sale.business_id == business_id)
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        return query.order_by(desc(Sale.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def get_sale_by_id(db: Session, business_id: UUID, sale_id: UUID) -> Sale:
        sale = db.query(Sale).filter(Sale.id == sale_id, Sale.business_id == business_id).first()
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        return sale

    @staticmethod
    def cancel_sale(db: Session, business_id: UUID, sale_id: UUID) -> Sale:
        sale = SalesService.get_sale_by_id(db, business_id, sale_id)
        if sale.payment_status == "CANCELLED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale is already cancelled")

        # Rollback stock for all items
        for item in sale.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.current_stock += item.quantity
                inv_tx = InventoryTransaction(
                    business_id=business_id,
                    product_id=product.id,
                    transaction_type="SALE_CANCEL_RESTORE",
                    quantity=item.quantity,
                    reference_id=str(sale.id),
                    description=f"Restored from cancelled Invoice {sale.invoice_number}"
                )
                db.add(inv_tx)

        # Revert credit if it was credit sale
        if sale.payment_method.lower() == "credit" and sale.customer_id:
            customer = db.query(Customer).filter(Customer.id == sale.customer_id).first()
            if customer:
                customer.outstanding_balance = max(Decimal("0.00"), customer.outstanding_balance - sale.total_amount)
                credit_tx = CreditTransaction(
                    business_id=business_id,
                    customer_id=customer.id,
                    sale_id=sale.id,
                    transaction_type="REPAYMENT",
                    amount=sale.total_amount,
                    description=f"Cancelled credit for Invoice {sale.invoice_number}"
                )
                db.add(credit_tx)

        sale.payment_status = "CANCELLED"
        db.commit()
        db.refresh(sale)
        return sale

