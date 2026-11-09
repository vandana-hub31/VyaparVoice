from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, SalesChartPoint, RecentTransaction, LowStockAlert
from app.services.dashboard_service import DashboardService
from app.utils.dependencies import get_current_business, get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_summary(db, business.id)

@router.get("/sales-chart", response_model=List[SalesChartPoint])
def get_sales_chart(
    days: int = Query(7, ge=1, le=90),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_sales_chart(db, business.id, days=days)

@router.get("/recent-transactions", response_model=List[RecentTransaction])
def get_recent_transactions(
    limit: int = Query(5, ge=1, le=50),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_recent_transactions(db, business.id, limit=limit)

@router.get("/low-stock", response_model=List[LowStockAlert])
def get_low_stock(
    limit: int = Query(10, ge=1, le=50),
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    return DashboardService.get_low_stock_products(db, business.id, limit=limit)

@router.get("/summary-ai")
def get_ai_daily_summary(
    lang: Optional[str] = None,
    business: Business = Depends(get_current_business),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    effective_lang = lang or current_user.preferred_language or "en"
    text = DashboardService.generate_daily_summary_text(db, business.id, lang=effective_lang)
    return {
        "language": effective_lang,
        "summary": text
    }
