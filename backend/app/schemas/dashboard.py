from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    today_sales: Decimal
    today_expenses: Decimal
    estimated_gross_profit: Decimal
    transaction_count: int
    outstanding_credit: Decimal
    total_products: int
    low_stock_count: int
    currency: str = "INR"

class SalesChartPoint(BaseModel):
    date: str
    sales: Decimal
    profit: Decimal

class RecentTransaction(BaseModel):
    id: UUID
    invoice_number: str
    customer_name: Optional[str] = None
    total_amount: Decimal
    payment_method: str
    payment_status: str
    created_at: datetime

class LowStockAlert(BaseModel):
    id: UUID
    product_name: str
    category: str
    current_stock: Decimal
    unit: str
    low_stock_threshold: Decimal

class TopProduct(BaseModel):
    product_id: UUID
    product_name: str
    quantity_sold: Decimal
    revenue: Decimal
    profit: Decimal

