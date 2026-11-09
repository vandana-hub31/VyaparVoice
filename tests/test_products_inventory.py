import uuid
import pytest

def get_auth_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "full_name": "Inventory Tester",
        "email": email,
        "password": "testpassword123",
        "preferred_language": "en"
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": "testpassword123"})
    return resp.json()["access_token"]

def test_product_crud_and_inventory(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add Product
    prod_payload = {
        "product_name": "Aashirvaad Atta 5kg",
        "SKU": "ATTA-5KG",
        "category": "Grains & Flours",
        "unit": "bag",
        "purchase_price": 210.0,
        "selling_price": 250.0,
        "current_stock": 20.0,
        "low_stock_threshold": 5.0
    }
    create_resp = client.post("/api/products", json=prod_payload, headers=headers)
    assert create_resp.status_code == 201
    prod = create_resp.json()
    prod_id = prod["id"]
    assert prod["current_stock"] == "20.00"

    # 2. Get Products list
    list_resp = client.get("/api/products", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. Adjust inventory
    adj_payload = {
        "product_id": prod_id,
        "quantity_change": 10.0,
        "transaction_type": "RESTOCK",
        "description": "Received supplier crate"
    }
    adj_resp = client.post("/api/inventory/adjust", json=adj_payload, headers=headers)
    assert adj_resp.status_code == 200
    assert adj_resp.json()["current_stock"] == "30.00"

    # 4. Reject negative inventory
    bad_adj = {
        "product_id": prod_id,
        "quantity_change": -50.0,
        "transaction_type": "ADJUSTMENT"
    }
    bad_resp = client.post("/api/inventory/adjust", json=bad_adj, headers=headers)
    assert bad_resp.status_code == 400
    assert "Insufficient stock" in bad_resp.json()["detail"]

    # 5. Check Inventory history
    hist_resp = client.get("/api/inventory/history", headers=headers)
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 2
