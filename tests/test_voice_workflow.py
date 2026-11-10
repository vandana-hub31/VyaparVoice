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
    # 1. English: Sell 2 kg rice for 120 -> CREATE_SALE
    p_sale_en = IntentService.parse_text("Sell 2 kg rice for 120")
    assert p_sale_en.intent == IntentType.CREATE_SALE
    assert p_sale_en.quantity == Decimal("2")
    assert p_sale_en.unit == "kg"
    assert p_sale_en.product_name == "rice"
    assert p_sale_en.price == Decimal("120")
    assert p_sale_en.language == "en"

    # 2. English: Add 10 packets of milk -> UPDATE_STOCK
    p_stock_en = IntentService.parse_text("Add 10 packets of milk")
    assert p_stock_en.intent == IntentType.UPDATE_STOCK
    assert p_stock_en.quantity == Decimal("10")
    assert p_stock_en.unit == "packets"
    assert "milk" in p_stock_en.product_name.lower()
    assert p_stock_en.language == "en"

    # 3. Hindi: 2 पैकेट दूध बेचो -> CREATE_SALE
    p_sale_hi = IntentService.parse_text("2 पैकेट दूध बेचो")
    assert p_sale_hi.intent == IntentType.CREATE_SALE
    assert p_sale_hi.quantity == Decimal("2")
    assert p_sale_hi.unit == "पैकेट"
    assert p_sale_hi.product_name == "दूध"
    assert p_sale_hi.language == "hi"

    # 4. Hindi: 10 पैकेट दूध जोड़ो -> UPDATE_STOCK
    p_stock_hi = IntentService.parse_text("10 पैकेट दूध जोड़ो")
    assert p_stock_hi.intent == IntentType.UPDATE_STOCK
    assert p_stock_hi.quantity == Decimal("10")
    assert p_stock_hi.unit == "पैकेट"
    assert p_stock_hi.product_name == "दूध"
    assert p_stock_hi.language == "hi"

    # 5. Kannada: 2 ಕೆಜಿ ಅಕ್ಕಿ ಮಾರಿರಿ -> CREATE_SALE
    p_sale_kn = IntentService.parse_text("2 ಕೆಜಿ ಅಕ್ಕಿ ಮಾರಿರಿ")
    assert p_sale_kn.intent == IntentType.CREATE_SALE
    assert p_sale_kn.quantity == Decimal("2")
    assert p_sale_kn.unit == "ಕೆಜಿ"
    assert p_sale_kn.product_name == "ಅಕ್ಕಿ"
    assert p_sale_kn.language == "kn"

    # 6. Kannada: 10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಹಾಕಿ -> UPDATE_STOCK (also test ಸೇರಿಸಿ)
    p_stock_kn = IntentService.parse_text("10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಹಾಕಿ")
    assert p_stock_kn.intent == IntentType.UPDATE_STOCK
    assert p_stock_kn.quantity == Decimal("10")
    assert p_stock_kn.unit == "ಪ್ಯಾಕೆಟ್"
    assert p_stock_kn.product_name == "ಹಾಲು"
    assert p_stock_kn.language == "kn"

    p_stock_kn_serisi = IntentService.parse_text("10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸೇರಿಸಿ")
    assert p_stock_kn_serisi.intent == IntentType.UPDATE_STOCK
    assert p_stock_kn_serisi.quantity == Decimal("10")
    assert p_stock_kn_serisi.language == "kn"

    # 7. Malayalam: 2 പാക്കറ്റ് പാൽ വിൽക്കുക -> CREATE_SALE
    p_sale_ml = IntentService.parse_text("2 പാക്കറ്റ് പാൽ വിൽക്കുക")
    assert p_sale_ml.intent == IntentType.CREATE_SALE
    assert p_sale_ml.quantity == Decimal("2")
    assert p_sale_ml.unit == "പാക്കറ്റ്"
    assert p_sale_ml.product_name == "പാൽ"
    assert p_sale_ml.language == "ml"

    # 8. Malayalam: 10 പാക്കറ്റ് പാൽ ചേർക്കുക -> UPDATE_STOCK
    p_stock_ml = IntentService.parse_text("10 പാക്കറ്റ് പാൽ ചേർക്കുക")
    assert p_stock_ml.intent == IntentType.UPDATE_STOCK
    assert p_stock_ml.quantity == Decimal("10")
    assert p_stock_ml.unit == "പാക്കറ്റ്"
    assert p_stock_ml.product_name == "പാൽ"
    assert p_stock_ml.language == "ml"

    # Additional queries in all supported languages
    p_en_sales = IntentService.parse_text("How much did I sell today?")
    assert p_en_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_en_sales.language == "en"

    p_kn_sales = IntentService.parse_text("ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?")
    assert p_kn_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_kn_sales.language == "kn"

    p_ml_sales = IntentService.parse_text("ഇന്ന് എത്ര രൂപയുടെ വിൽപ്പനയായി?")
    assert p_ml_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_ml_sales.language == "ml"

    p_hi_sales = IntentService.parse_text("आज कितनी बिक्री हुई?")
    assert p_hi_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_hi_sales.language == "hi"

    p_ta_sales = IntentService.parse_text("இன்று எவ்வளவு விற்றோம்?")
    assert p_ta_sales.intent == IntentType.GET_TODAYS_SALES
    assert p_ta_sales.language == "ta"

    # Code-mixed Hinglish & Romanized
    p_hinglish = IntentService.parse_text("10 packet milk add karo")
    assert p_hinglish.intent == IntentType.UPDATE_STOCK
    assert p_hinglish.quantity == Decimal("10")
    assert p_hinglish.language == "hi"

    # Unknown Intent Handling
    p_unknown = IntentService.parse_text("Abracadabra random nonsense text")
    assert p_unknown.intent == IntentType.UNKNOWN_INTENT
    assert p_unknown.is_ambiguous is True

    # Additional intents
    p_credit = IntentService.parse_text("Ramesh owes me 500")
    assert p_credit.intent == IntentType.CREATE_CREDIT
    assert p_credit.amount == Decimal("500")

    p_inv = IntentService.parse_text("show inventory")
    assert p_inv.intent == IntentType.GET_INVENTORY

    p_top = IntentService.parse_text("best selling products")
    assert p_top.intent == IntentType.GET_TOP_PRODUCTS

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

def test_voice_credit_and_user_isolation(client):
    token_a = get_auth_token(client)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    token_b = get_auth_token(client)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A adds customer Suresh
    c_resp = client.post("/api/customers", json={"customer_name": "Suresh Kumar", "phone": "9876543210"}, headers=headers_a)
    assert c_resp.status_code == 201

    # 2. User A triggers voice command to give credit
    cmd_resp = client.post("/api/voice/command", json={
        "transcription": "Suresh owes me 350",
        "language": "en"
    }, headers=headers_a)
    assert cmd_resp.status_code == 200
    cmd_data = cmd_resp.json()
    assert cmd_data["execution_status"] == "PENDING_CONFIRMATION"
    token = cmd_data["confirmation_token"]

    # 3. User B attempts to confirm User A's token -> Must be rejected with 403 Forbidden
    hack_resp = client.post("/api/voice/confirm", json={
        "confirmation_token": token,
        "confirmed": True
    }, headers=headers_b)
    assert hack_resp.status_code == 403

    # 4. User A confirms their own action -> Must succeed
    ok_resp = client.post("/api/voice/confirm", json={
        "confirmation_token": token,
        "confirmed": True
    }, headers=headers_a)
    assert ok_resp.status_code == 200
    ok_data = ok_resp.json()
    assert ok_data["execution_status"] == "SUCCESS"
    assert ok_data["data"]["new_balance"] == 350.0

def test_audio_upload_validation_and_synthesis(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Invalid file format upload must return 400 Bad Request
    bad_upload = client.post(
        "/api/voice/transcribe",
        files={"file": ("notes.txt", b"just some text", "text/plain")},
        data={"language": "indic-auto"},
        headers=headers
    )
    assert bad_upload.status_code == 400
    assert "audio file" in bad_upload.json()["detail"].lower()

    # 2. Gnani connectivity check endpoint
    status_resp = client.get("/api/voice/gnani/status")
    assert status_resp.status_code == 200
    assert "status" in status_resp.json()

    # 3. Speech synthesis endpoint
    synth_resp = client.post(
        "/api/voice/synthesize",
        json={
            "text": "ನಮಸ್ಕಾರ",
            "language": "kn-IN"
        },
        headers=headers
    )
    # If API key configured and reachable, returns 200, else handled error
    assert synth_resp.status_code in [200, 500]
    if synth_resp.status_code == 200:
        assert "audio_base64" in synth_resp.json()
