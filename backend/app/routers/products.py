from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService
from app.utils.dependencies import get_current_business

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=List[ProductResponse])
def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    low_stock_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ProductService.get_products(
        db,
        business.id,
        search=search,
        category=category,
        low_stock_only=low_stock_only,
        limit=limit,
        offset=offset
    )

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ProductService.create_product(db, business.id, data)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ProductService.get_product_by_id(db, business.id, product_id)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return ProductService.update_product(db, business.id, product_id, data)

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    ProductService.delete_product(db, business.id, product_id)
    return {"status": "success", "message": "Product deleted successfully"}
