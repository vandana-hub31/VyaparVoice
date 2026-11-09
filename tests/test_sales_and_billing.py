import uuid
from decimal import Decimal

def get_auth_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "full_name": "Sales Tester",
        "email": email,
        "password": "testpassword123",
        "preferred_language": "hi"
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": "testpassword123"})
    return resp.json()["access_token"]

def test_sale_creation_and_inventory_deduction(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Product
    prod_resp = client.post("/api/products", json={
        "product_name": "Tata Tea 250g",
        "category": "Beverages",
        "unit": "pkt",
        "purchase_price": 120.0,
        "selling_price": 150.0,
        "current_stock": 10.0,
        "low_stock_threshold": 3.0
    }, headers=headers)
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["id"]

    # 2. Perform Sale of 3 packets
    sale_payload = {
        "items": [
            {"product_id": prod_id, "quantity": 3.0}
        ],
        "discount": 10.0,
        "tax_rate_percent": 5.0,
        "payment_method": "Cash",
        "idempotency_key": "unique-idem-12345"
    }
    sale_resp = client.post("/api/sales", json=sale_payload, headers=headers)
    assert sale_resp.status_code == 201
    sale_data = sale_resp.json()

    # Verify server-side calculation:
    # Subtotal: 3 * 150 = 450
    # Taxable: 450 - 10 = 440
    # Tax: 5% of 440 = 22
    # Total: 440 + 22 = 462
    assert Decimal(sale_data["subtotal"]) == Decimal("450.00")
    assert Decimal(sale_data["discount"]) == Decimal("10.00")
    assert Decimal(sale_data["tax"]) == Decimal("22.00")
    assert Decimal(sale_data["total_amount"]) == Decimal("462.00")
    sale_id = sale_data["id"]

    # Verify inventory was deducted: 10 - 3 = 7
    prod_check = client.get(f"/api/products/{prod_id}", headers=headers)
    assert Decimal(prod_check.json()["current_stock"]) == Decimal("7.00")

    # 3. Test Idempotency: Repeating exact same request returns existing sale without duplicate deduction
    dup_resp = client.post("/api/sales", json=sale_payload, headers=headers)
    assert dup_resp.status_code == 201
    assert dup_resp.json()["id"] == sale_id
    # Stock should remain 7.00
    prod_check_2 = client.get(f"/api/products/{prod_id}", headers=headers)
    assert Decimal(prod_check_2.json()["current_stock"]) == Decimal("7.00")

    # 4. Cancel Sale and verify stock rollback
    cancel_resp = client.post(f"/api/sales/{sale_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["payment_status"] == "CANCELLED"

    # Stock should be restored to 10.00
    prod_restored = client.get(f"/api/products/{prod_id}", headers=headers)
    assert Decimal(prod_restored.json()["current_stock"]) == Decimal("10.00")

