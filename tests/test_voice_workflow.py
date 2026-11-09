import uuid
from decimal import Decimal
from app.services.intent_service import IntentService
from app.schemas.intent import IntentType

def get_auth_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "full_name": "Voice Tester",
        "email": email,
        "password": "testpassword123",
        "preferred_language": "kn"
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": "testpassword123"})
    return resp.json()["access_token"]

def test_intent_parsing_multilingual():
    # English
    p_en_sales = IntentService.parse_text("How much did I sell today?")
    assert p_en_sales.intent == IntentType.GET_TODAYS_SALES

    p_en_stock = IntentService.parse_text("Add 10 packets of milk")
    assert p_en_stock.intent == IntentType.UPDATE_STOCK
    assert p_en_stock.quantity == Decimal("10")
    assert "milk" in p_en_stock.product_name.lower()
    assert p_en_stock.requires_confirmation is True

    # Kannada
    p_kn_sales = IntentService.parse_text("ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?")
    assert p_kn_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_kn_sales.language == "kn"

    # Malayalam
    p_ml_sales = IntentService.parse_text("ഇന്ന് എത്ര രൂപയുടെ വിൽപ്പനയായി?")
    assert p_ml_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_ml_sales.language == "ml"

    # Hindi
    p_hi_sales = IntentService.parse_text("आज कितनी बिक्री हुई?")
    assert p_hi_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_hi_sales.language == "hi"

    # Tamil
    p_ta_sales = IntentService.parse_text("இன்று எவ்வளவு விற்றோம்?")
    assert p_ta_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_ta_sales.language == "ta"

    # Code-mixed Hinglish
    p_hinglish = IntentService.parse_text("10 packet milk add karo")
    assert p_hinglish.intent == IntentType.UPDATE_STOCK
    assert p_hinglish.quantity == Decimal("10")

def test_voice_confirmation_workflow(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a product first
    client.post("/api/products", json={
        "product_name": "Nandini Milk",
        "category": "Dairy",
        "unit": "pkt",
        "purchase_price": 22.0,
        "selling_price": 25.0,
        "current_stock": 10.0,
        "low_stock_threshold": 5.0
    }, headers=headers)

    # 2. Trigger voice command to add 10 packets of milk
    cmd_resp = client.post("/api/voice/command", json={
        "transcription": "Add 10 packets of Nandini Milk",
        "language": "en"
    }, headers=headers)
    assert cmd_resp.status_code == 200
    cmd_data = cmd_resp.json()
    assert cmd_data["execution_status"] == "PENDING_CONFIRMATION"
    assert cmd_data["confirmation_token"] is not None
    assert "Nandini Milk" in cmd_data["response_text"]
    conf_token = cmd_data["confirmation_token"]

    # 3. Confirm the action
    confirm_resp = client.post("/api/voice/confirm", json={
        "confirmation_token": conf_token,
        "confirmed": True
    }, headers=headers)
    assert confirm_resp.status_code == 200
    conf_data = confirm_resp.json()
    assert conf_data["execution_status"] == "SUCCESS"
    assert "20" in conf_data["response_text"]
    assert conf_data["data"]["new_stock"] == 20.0

    # 4. Check voice interaction history was logged in PostgreSQL
    hist_resp = client.get("/api/voice/history", headers=headers)
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1
