from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.schemas.inventory import InventoryAdjustment, InventoryTransactionResponse
from app.schemas.product import ProductResponse
from app.services.product_service import ProductService
from app.utils.dependencies import get_current_business

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.get("", response_model=List[ProductResponse])
def get_inventory_status(
    low_stock_only: bool = False,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ProductService.get_products(db, business.id, low_stock_only=low_stock_only)

@router.post("/adjust", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def adjust_inventory(
    adj: InventoryAdjustment,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ProductService.adjust_stock(db, business.id, adj)

@router.get("/history", response_model=List[InventoryTransactionResponse])
def get_inventory_history(
    limit: int = Query(50, ge=1, le=200),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    txs = ProductService.get_inventory_history(db, business.id, limit=limit)
    # enrich product_name
    results = []
    for t in txs:
        p_name = t.product.product_name if t.product else "Deleted Product"
        item = InventoryTransactionResponse.model_validate(t)
        item.product_name = p_name
        results.append(item)
    return results
