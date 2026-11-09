from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.schemas.sale import SaleCreate, SaleResponse, SaleDetailResponse, SaleItemResponse
from app.services.sales_service import SalesService
from app.utils.dependencies import get_current_business

router = APIRouter(prefix="/api/sales", tags=["Sales"])

@router.get("", response_model=List[SaleResponse])
def get_sales(
    customer_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    sales = SalesService.get_sales(db, business.id, customer_id=customer_id, limit=limit, offset=offset)
    results = []
    for s in sales:
        c_name = s.customer.customer_name if s.customer else None
        item = SaleResponse.model_validate(s)
        item.customer_name = c_name
        item.items_count = len(s.items)
        results.append(item)
    return results

@router.post("", response_model=SaleDetailResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    data: SaleCreate,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    sale = SalesService.create_sale(db, business.id, data)
    c_name = sale.customer.customer_name if sale.customer else None
    
    items_resp = []
    for si in sale.items:
        p_name = si.product.product_name if si.product else None
        sir = SaleItemResponse.model_validate(si)
        sir.product_name = p_name
        items_resp.append(sir)
        
    res = SaleDetailResponse.model_validate(sale)
    res.customer_name = c_name
    res.items = items_resp
    return res

@router.get("/{sale_id}", response_model=SaleDetailResponse)
def get_sale_detail(
    sale_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    sale = SalesService.get_sale_by_id(db, business.id, sale_id)
    c_name = sale.customer.customer_name if sale.customer else None
    
    items_resp = []
    for si in sale.items:
        p_name = si.product.product_name if si.product else None
        sir = SaleItemResponse.model_validate(si)
        sir.product_name = p_name
        items_resp.append(sir)
        
    res = SaleDetailResponse.model_validate(sale)
    res.customer_name = c_name
    res.items = items_resp
    return res

@router.post("/{sale_id}/cancel", response_model=SaleResponse)
def cancel_sale(
    sale_id: UUID,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    sale = SalesService.cancel_sale(db, business.id, sale_id)
    c_name = sale.customer.customer_name if sale.customer else None
    res = SaleResponse.model_validate(sale)
    res.customer_name = c_name
    return res
