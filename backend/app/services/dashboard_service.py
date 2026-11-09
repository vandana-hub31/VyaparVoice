from uuid import UUID
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.sale import Sale, SaleItem
from app.models.expense import Expense
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.dashboard import DashboardSummary, SalesChartPoint, RecentTransaction, LowStockAlert, TopProduct

class DashboardService:
    @staticmethod
    def get_summary(db: Session, business_id: UUID) -> DashboardSummary:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's sales (non-cancelled)
        sales_today = db.query(
            func.coalesce(func.sum(Sale.total_amount), Decimal("0.00")),
            func.count(Sale.id)
        ).filter(
            Sale.business_id == business_id,
            Sale.created_at >= today_start,
            Sale.payment_status != "CANCELLED"
        ).first()

        today_sales = sales_today[0]
        tx_count = sales_today[1]

        # Today's expenses
        today_expenses = db.query(
            func.coalesce(func.sum(Expense.amount), Decimal("0.00"))
        ).filter(
            Expense.business_id == business_id,
            Expense.created_at >= today_start
        ).scalar() or Decimal("0.00")

        # Today's gross profit: (unit_price - purchase_price_snapshot) * quantity
        profit_query = db.query(
            func.coalesce(
                func.sum((SaleItem.unit_price - SaleItem.purchase_price_snapshot) * SaleItem.quantity),
                Decimal("0.00")
            )
        ).join(Sale, Sale.id == SaleItem.sale_id).filter(
            Sale.business_id == business_id,
            Sale.created_at >= today_start,
            Sale.payment_status != "CANCELLED"
        ).scalar() or Decimal("0.00")

        # Customer outstanding credit
        outstanding_credit = db.query(
            func.coalesce(func.sum(Customer.outstanding_balance), Decimal("0.00"))
        ).filter(Customer.business_id == business_id).scalar() or Decimal("0.00")

        # Products
        total_products = db.query(func.count(Product.id)).filter(Product.business_id == business_id).scalar() or 0
        low_stock_count = db.query(func.count(Product.id)).filter(
            Product.business_id == business_id,
            Product.current_stock <= Product.low_stock_threshold
        ).scalar() or 0

        return DashboardSummary(
            today_sales=today_sales,
            today_expenses=today_expenses,
            estimated_gross_profit=profit_query,
            transaction_count=tx_count,
            outstanding_credit=outstanding_credit,
            total_products=total_products,
            low_stock_count=low_stock_count,
            currency="INR"
        )

    @staticmethod
    def get_sales_chart(db: Session, business_id: UUID, days: int = 7) -> List[SalesChartPoint]:
        chart_points = []
        today = datetime.now(timezone.utc).date()
        
        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)

            sales_amt = db.query(
                func.coalesce(func.sum(Sale.total_amount), Decimal("0.00"))
            ).filter(
                Sale.business_id == business_id,
                Sale.created_at >= day_start,
                Sale.created_at < day_end,
                Sale.payment_status != "CANCELLED"
            ).scalar() or Decimal("0.00")

            profit_amt = db.query(
                func.coalesce(
                    func.sum((SaleItem.unit_price - SaleItem.purchase_price_snapshot) * SaleItem.quantity),
                    Decimal("0.00")
                )
            ).join(Sale, Sale.id == SaleItem.sale_id).filter(
                Sale.business_id == business_id,
                Sale.created_at >= day_start,
                Sale.created_at < day_end,
                Sale.payment_status != "CANCELLED"
            ).scalar() or Decimal("0.00")

            chart_points.append(SalesChartPoint(
                date=target_date.strftime("%d %b"),
                sales=sales_amt,
                profit=profit_amt
            ))

        return chart_points

    @staticmethod
    def get_recent_transactions(db: Session, business_id: UUID, limit: int = 5) -> List[RecentTransaction]:
        sales = db.query(Sale).filter(Sale.business_id == business_id)\
            .order_by(desc(Sale.created_at))\
            .limit(limit).all()

        results = []
        for s in sales:
            c_name = s.customer.customer_name if s.customer else "Walk-in Customer"
            results.append(RecentTransaction(
                id=s.id,
                invoice_number=s.invoice_number,
                customer_name=c_name,
                total_amount=s.total_amount,
                payment_method=s.payment_method,
                payment_status=s.payment_status,
                created_at=s.created_at
            ))
        return results

    @staticmethod
    def get_low_stock_products(db: Session, business_id: UUID, limit: int = 10) -> List[LowStockAlert]:
        products = db.query(Product).filter(
            Product.business_id == business_id,
            Product.current_stock <= Product.low_stock_threshold
        ).order_by(Product.current_stock.asc()).limit(limit).all()

        return [
            LowStockAlert(
                id=p.id,
                product_name=p.product_name,
                category=p.category,
                current_stock=p.current_stock,
                unit=p.unit,
                low_stock_threshold=p.low_stock_threshold
            ) for p in products
        ]

    @staticmethod
    def get_top_products(db: Session, business_id: UUID, limit: int = 5) -> List[TopProduct]:
        rows = db.query(
            Product.id,
            Product.product_name,
            func.coalesce(func.sum(SaleItem.quantity), Decimal("0.00")).label("qty"),
            func.coalesce(func.sum(SaleItem.total_amount), Decimal("0.00")).label("revenue"),
            func.coalesce(
                func.sum((SaleItem.unit_price - SaleItem.purchase_price_snapshot) * SaleItem.quantity),
                Decimal("0.00")
            ).label("profit")
        ).join(SaleItem, SaleItem.product_id == Product.id)\
         .join(Sale, Sale.id == SaleItem.sale_id)\
         .filter(
             Product.business_id == business_id,
             Sale.payment_status != "CANCELLED"
         )\
         .group_by(Product.id, Product.product_name)\
         .order_by(desc("revenue"))\
         .limit(limit).all()

        return [
            TopProduct(
                product_id=r[0],
                product_name=r[1],
                quantity_sold=r[2],
                revenue=r[3],
                profit=r[4]
            ) for r in rows
        ]

    @staticmethod
    def generate_daily_summary_text(db: Session, business_id: UUID, lang: str = "en") -> str:
        summary = DashboardService.get_summary(db, business_id)
        low_stocks = DashboardService.get_low_stock_products(db, business_id, limit=3)
        low_stock_names = ", ".join([p.product_name for p in low_stocks]) or "None"

        if lang == "kn":
            return (
                f"ಇವತ್ತಿನ ವ್ಯವಹಾರ ಸಾರಾಂಶ: ಒಟ್ಟು ಮಾರಾಟ ₹{summary.today_sales:,.2f} "
                f"({summary.transaction_count} ಬಿಲ್‌ಗಳು). ಖರ್ಚು ₹{summary.today_expenses:,.2f}. "
                f"ಅಂದಾಜು ಲಾಭ ₹{summary.estimated_gross_profit:,.2f}. "
                f"ಸ್ಟಾಕ್ ಕಡಿಮೆ ಇರುವ ಸರಕುಗಳು: {low_stock_names}."
            )
        elif lang == "ml":
            return (
                f"ഇന്നത്തെ ബിസിനസ്സ് വിവരണം: ആകെ വിൽപ്പന ₹{summary.today_sales:,.2f} "
                f"({summary.transaction_count} ഇടപാടുകൾ). ചെലവുകൾ ₹{summary.today_expenses:,.2f}. "
                f"ലാഭം ഏകദേശം ₹{summary.estimated_gross_profit:,.2f}. "
                f"കുറഞ്ഞ സ്റ്റോക്കുള്ള ഉൽപ്പന്നങ്ങൾ: {low_stock_names}."
            )
        elif lang == "hi":
            return (
                f"आज का व्यापार सारांश: कुल बिक्री ₹{summary.today_sales:,.2f} "
                f"({summary.transaction_count} बिल). कुल खर्चे ₹{summary.today_expenses:,.2f}. "
                f"अनुमानित सकल लाभ ₹{summary.estimated_gross_profit:,.2f}. "
                f"कम स्टॉक वाले उत्पाद: {low_stock_names}."
            )
        elif lang == "ta":
            return (
                f"இன்றைய வியாபார சுருக்கம்: மொத்த விற்பனை ₹{summary.today_sales:,.2f} "
                f"({summary.transaction_count} பில்கள்). செலவுகள் ₹{summary.today_expenses:,.2f}. "
                f"மதிப்பிடப்பட்ட மொத்த லாபம் ₹{summary.estimated_gross_profit:,.2f}. "
                f"குறைந்த இருப்பு உள்ள பொருட்கள்: {low_stock_names}."
            )
        else:
            return (
                f"Today, your total sales were ₹{summary.today_sales:,.2f} across {summary.transaction_count} transactions. "
                f"Recorded expenses were ₹{summary.today_expenses:,.2f}, and estimated gross profit was ₹{summary.estimated_gross_profit:,.2f}. "
                f"{summary.low_stock_count} products are running low in stock."
            )

