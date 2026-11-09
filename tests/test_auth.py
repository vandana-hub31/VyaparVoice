import uuid

def test_register_and_login(client):
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "full_name": "Test Shopkeeper",
        "email": unique_email,
        "password": "securepassword123",
        "phone": "9876543210",
        "preferred_language": "kn"
    }

    # 1. Register
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == unique_email
    assert user_data["full_name"] == "Test Shopkeeper"
    assert "hashed_password" not in user_data

    # 2. Login
    login_resp = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "securepassword123"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Authenticated profile check
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email

    # 4. Check auto-created business
    b_resp = client.get("/api/businesses/current", headers={"Authorization": f"Bearer {token}"})
    assert b_resp.status_code == 200
    b_data = b_resp.json()
    assert "Test Shopkeeper" in b_data["business_name"]
    assert b_data["currency"] == "INR"
    assert b_data["timezone"] == "Asia/Kolkata"
