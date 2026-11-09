from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.schemas.dashboard import SalesChartPoint, TopProduct
from app.services.dashboard_service import DashboardService
from app.utils.dependencies import get_current_business

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/daily", response_model=List[SalesChartPoint])
def get_daily_analytics(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_sales_chart(db, business.id, days=7)

@router.get("/weekly", response_model=List[SalesChartPoint])
def get_weekly_analytics(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_sales_chart(db, business.id, days=30)

@router.get("/monthly", response_model=List[SalesChartPoint])
def get_monthly_analytics(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_sales_chart(db, business.id, days=90)

@router.get("/top-products", response_model=List[TopProduct])
def get_top_products(
    limit: int = Query(5, ge=1, le=20),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_top_products(db, business.id, limit=limit)

