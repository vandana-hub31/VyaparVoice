import uuid
from decimal import Decimal

def get_auth_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "full_name": "Ledger Tester",
        "email": email,
        "password": "testpassword123",
        "preferred_language": "ml"
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": "testpassword123"})
    return resp.json()["access_token"]

def test_customers_credit_and_expenses(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add Customer
    cust_resp = client.post("/api/customers", json={
        "customer_name": "Anil Kumar",
        "phone": "9845099887",
        "address": "Indiranagar, Bengaluru",
        "initial_balance": 500.0
    }, headers=headers)
    assert cust_resp.status_code == 201
    cust = cust_resp.json()
    cust_id = cust["id"]
    assert Decimal(cust["outstanding_balance"]) == Decimal("500.00")

    # 2. Add Product
    prod_resp = client.post("/api/products", json={
        "product_name": "Basmati Rice 1kg",
        "category": "Grains",
        "unit": "kg",
        "purchase_price": 90.0,
        "selling_price": 120.0,
        "current_stock": 50.0,
        "low_stock_threshold": 5.0
    }, headers=headers)
    prod_id = prod_resp.json()["id"]

    # 3. Credit Sale to Anil Kumar
    sale_resp = client.post("/api/sales", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": 2.0}],
        "payment_method": "Credit"
    }, headers=headers)
    assert sale_resp.status_code == 201
    # Sale was 2 * 120 = 240
    # Customer balance becomes 500 + 240 = 740

    cust_check = client.get(f"/api/customers/{cust_id}", headers=headers)
    assert Decimal(cust_check.json()["outstanding_balance"]) == Decimal("740.00")

    # 4. Record Repayment of 300
    repay_resp = client.post(f"/api/customers/{cust_id}/repayments", json={
        "amount": 300.0,
        "payment_method": "UPI",
        "description": "Google Pay repayment"
    }, headers=headers)
    assert repay_resp.status_code == 201

    # Balance becomes 740 - 300 = 440
    cust_after_repay = client.get(f"/api/customers/{cust_id}", headers=headers)
    assert Decimal(cust_after_repay.json()["outstanding_balance"]) == Decimal("440.00")

    # 5. Customer Ledger has 3 entries: initial (500), credit sale (240), repayment (300)
    ledger_resp = client.get(f"/api/customers/{cust_id}/ledger", headers=headers)
    assert ledger_resp.status_code == 200
    assert len(ledger_resp.json()) == 3

    # 6. Add Expense
    exp_resp = client.post("/api/expenses", json={
        "category": "Electricity",
        "description": "Monthly shop electricity",
        "amount": 450.0,
        "payment_method": "UPI"
    }, headers=headers)
    assert exp_resp.status_code == 201

    # 7. Check Dashboard Summary
    dash_resp = client.get("/api/dashboard/summary", headers=headers)
    assert dash_resp.status_code == 200
    summary = dash_resp.json()
    assert Decimal(summary["today_sales"]) == Decimal("240.00")
    assert Decimal(summary["today_expenses"]) == Decimal("450.00")
    # Gross profit: (120 - 90) * 2 = 60
    assert Decimal(summary["estimated_gross_profit"]) == Decimal("60.00")
    assert Decimal(summary["outstanding_credit"]) == Decimal("440.00")

