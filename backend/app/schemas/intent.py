from enum import Enum
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    GET_TODAYS_SALES = "GET_TODAYS_SALES"
    GET_SALES_SUMMARY = "GET_SALES_SUMMARY"
    GET_PROFIT_SUMMARY = "GET_PROFIT_SUMMARY"
    GET_EXPENSE_SUMMARY = "GET_EXPENSE_SUMMARY"
    GET_LOW_STOCK = "GET_LOW_STOCK"
    GET_TOP_PRODUCTS = "GET_TOP_PRODUCTS"
    ADD_PRODUCT = "ADD_PRODUCT"
    UPDATE_STOCK = "UPDATE_STOCK"
    CREATE_SALE = "CREATE_SALE"
    ADD_EXPENSE = "ADD_EXPENSE"
    ADD_CUSTOMER = "ADD_CUSTOMER"
    CREATE_CREDIT = "CREATE_CREDIT"
    RECORD_REPAYMENT = "RECORD_REPAYMENT"
    GET_CUSTOMER_BALANCE = "GET_CUSTOMER_BALANCE"
    GET_CUSTOMER_HISTORY = "GET_CUSTOMER_HISTORY"
    GET_INVENTORY = "GET_INVENTORY"
    UNKNOWN_INTENT = "UNKNOWN_INTENT"

class IntentItem(BaseModel):
    product_name: str
    quantity: Decimal
    unit_price: Optional[Decimal] = None
    unit: Optional[str] = "pcs"

class ParsedIntent(BaseModel):
    intent: IntentType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_confirmation: bool = False
    language: str = "en"  # en, hi, kn, ml, etc.
    
    # Entities
    product_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    price: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    amount: Optional[Decimal] = None
    payment_method: Optional[str] = "Cash"
    expense_category: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[IntentItem]] = None
    time_period: Optional[str] = "today"  # today, weekly, monthly
    
    # Clarification
    is_ambiguous: bool = False
    clarification_question: Optional[str] = None
