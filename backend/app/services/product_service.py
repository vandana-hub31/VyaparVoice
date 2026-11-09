from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.inventory import InventoryTransaction
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.inventory import InventoryAdjustment

class ProductService:
    @staticmethod
    def get_products(
        db: Session,
        business_id: UUID,
        search: Optional[str] = None,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Product]:
        query = db.query(Product).filter(Product.business_id == business_id)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(or_(Product.product_name.ilike(search_term), Product.SKU.ilike(search_term)))
        if category and category != "All":
            query = query.filter(Product.category == category)
        if low_stock_only:
            query = query.filter(Product.current_stock <= Product.low_stock_threshold)
        
        return query.order_by(Product.product_name.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_product_by_id(db: Session, business_id: UUID, product_id: UUID) -> Product:
        product = db.query(Product).filter(Product.id == product_id, Product.business_id == business_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    @staticmethod
    def get_product_by_name(db: Session, business_id: UUID, name: str) -> Optional[Product]:
        return db.query(Product).filter(
            Product.business_id == business_id,
            Product.product_name.ilike(name.strip())
        ).first()

    @staticmethod
    def create_product(db: Session, business_id: UUID, data: ProductCreate) -> Product:
        existing = db.query(Product).filter(
            Product.business_id == business_id,
            Product.product_name.ilike(data.product_name.strip())
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with name '{data.product_name}' already exists"
            )

        product = Product(
            business_id=business_id,
            product_name=data.product_name.strip(),
            SKU=data.SKU.strip() if data.SKU else None,
            category=data.category.strip(),
            unit=data.unit.strip().lower(),
            purchase_price=data.purchase_price,
            selling_price=data.selling_price,
            current_stock=data.current_stock,
            low_stock_threshold=data.low_stock_threshold
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Log initial inventory transaction if initial stock > 0
        if product.current_stock > 0:
            inv_tx = InventoryTransaction(
                business_id=business_id,
                product_id=product.id,
                transaction_type="RESTOCK",
                quantity=product.current_stock,
                description="Initial stock on product creation"
            )
            db.add(inv_tx)
            db.commit()

        return product

    @staticmethod
    def update_product(db: Session, business_id: UUID, product_id: UUID, data: ProductUpdate) -> Product:
        product = ProductService.get_product_by_id(db, business_id, product_id)
        
        update_dict = data.model_dump(exclude_unset=True)
        stock_change = None
        
        if "current_stock" in update_dict and update_dict["current_stock"] is not None:
            new_stock = Decimal(str(update_dict["current_stock"]))
            if new_stock < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock cannot be negative")
            stock_change = new_stock - product.current_stock
            product.current_stock = new_stock
            del update_dict["current_stock"]

        for key, val in update_dict.items():
            if val is not None:
                setattr(product, key, val)

        db.commit()
        db.refresh(product)

        if stock_change is not None and stock_change != 0:
            inv_tx = InventoryTransaction(
                business_id=business_id,
                product_id=product.id,
                transaction_type="ADJUSTMENT",
                quantity=stock_change,
                description="Manual stock edit"
            )
            db.add(inv_tx)
            db.commit()

        return product

    @staticmethod
    def delete_product(db: Session, business_id: UUID, product_id: UUID) -> bool:
        product = ProductService.get_product_by_id(db, business_id, product_id)
        db.delete(product)
        db.commit()
        return True

    @staticmethod
    def adjust_stock(db: Session, business_id: UUID, adj: InventoryAdjustment) -> Product:
        product = ProductService.get_product_by_id(db, business_id, adj.product_id)
        new_stock = product.current_stock + adj.quantity_change
        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.product_name}'. Available: {product.current_stock}, Requested reduction: {abs(adj.quantity_change)}"
            )

        product.current_stock = new_stock
        inv_tx = InventoryTransaction(
            business_id=business_id,
            product_id=product.id,
            transaction_type=adj.transaction_type,
            quantity=adj.quantity_change,
            description=adj.description or f"Stock adjustment of {adj.quantity_change} {product.unit}"
        )
        db.add(inv_tx)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_inventory_history(db: Session, business_id: UUID, limit: int = 50) -> List[InventoryTransaction]:
        return db.query(InventoryTransaction)\
            .filter(InventoryTransaction.business_id == business_id)\
            .order_by(desc(InventoryTransaction.created_at))\
            .limit(limit)\
            .all()

