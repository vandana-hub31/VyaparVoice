import uuid
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.business import Business
from app.models.voice import VoiceInteraction
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.intent import IntentType, ParsedIntent
from app.schemas.voice import VoiceCommandResponse, ActionConfirmationDetails
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.schemas.inventory import InventoryAdjustment
from app.schemas.expense import ExpenseCreate
from app.schemas.customer import CustomerCreate, RepaymentCreate
from app.services.intent_service import IntentService
from app.services.dashboard_service import DashboardService
from app.services.product_service import ProductService
from app.services.sales_service import SalesService
from app.services.customer_service import CustomerService
from app.services.expense_service import ExpenseService
from app.services.gnani_service import GnaniService

# Pending actions in-memory store: token -> dict
_pending_actions: Dict[str, Dict[str, Any]] = {}

class VoiceOrchestrator:
    @staticmethod
    def _create_confirmation(
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        action_type: str,
        summary: str,
        params: Dict[str, Any],
        lang: str
    ) -> tuple[str, ActionConfirmationDetails]:
        token = secrets.token_urlsafe(16)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        _pending_actions[token] = {
            "token": token,
            "business_id": business_id,
            "user_id": user_id,
            "action_type": action_type,
            "summary": summary,
            "params": params,
            "lang": lang,
            "expires_at": expires_at
        }

        details = ActionConfirmationDetails(
            action_type=action_type,
            summary=summary,
            params=params,
            expires_at=expires_at
        )
        return token, details

    @staticmethod
    async def process_command(
        db: Session,
        business: Business,
        user: User,
        transcription: str,
        lang: Optional[str] = "auto",
        idempotency_key: Optional[str] = None
    ) -> VoiceCommandResponse:
        # Normalize request language hint if passed from frontend or STT
        req_lang = None
        if lang and lang.lower() not in ["auto", "indic-auto"]:
            clean_l = lang.lower().split("-")[0].strip()
            if clean_l in ["kn", "ml", "hi", "ta", "en"]:
                req_lang = clean_l

        user_hint = req_lang or user.preferred_language or "en"
        parsed = IntentService.parse_text(transcription, user_lang=user_hint)
        effective_lang = parsed.language

        # READ-ONLY ACTIONS
        if parsed.intent == IntentType.GET_TODAYS_SALES:
            summary = DashboardService.get_summary(db, business.id)
            if effective_lang == "kn":
                resp_text = f"ಇವತ್ತಿನ ಒಟ್ಟು ಮಾರಾಟ ₹{summary.today_sales:,.2f}. ಒಟ್ಟು {summary.transaction_count} ಬಿಲ್‌ಗಳು ದಾಖಲಾಗಿವೆ."
            elif effective_lang == "ml":
                resp_text = f"ഇന്നത്തെ ആകെ വിൽപ്പന ₹{summary.today_sales:,.2f} ആണ് ({summary.transaction_count} ഇടപാടുകൾ)."
            elif effective_lang == "hi":
                resp_text = f"आज की कुल बिक्री ₹{summary.today_sales:,.2f} रही, जिसमें कुल {summary.transaction_count} बिल शामिल हैं।"
            elif effective_lang == "ta":
                resp_text = f"இன்று மொத்த விற்பனை ₹{summary.today_sales:,.2f} ({summary.transaction_count} பில்கள்)."
            else:
                resp_text = f"Today's total sales are ₹{summary.today_sales:,.2f} across {summary.transaction_count} transactions."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"today_sales": float(summary.today_sales), "transactions": summary.transaction_count}
            )

        elif parsed.intent == IntentType.GET_PROFIT_SUMMARY:
            summary = DashboardService.get_summary(db, business.id)
            if effective_lang == "kn":
                resp_text = f"ಇವತ್ತಿನ ಅಂದಾಜು ಒಟ್ಟು ಲಾಭ ₹{summary.estimated_gross_profit:,.2f} ಆಗಿದೆ."
            elif effective_lang == "ml":
                resp_text = f"ഇന്നത്തെ ഏകദേശ ലാഭം ₹{summary.estimated_gross_profit:,.2f} ആണ്."
            elif effective_lang == "hi":
                resp_text = f"आज का अनुमानित सकल लाभ ₹{summary.estimated_gross_profit:,.2f} है।"
            elif effective_lang == "ta":
                resp_text = f"இன்றைய மதிப்பிடப்பட்ட மொத்த லாபம் ₹{summary.estimated_gross_profit:,.2f}."
            else:
                resp_text = f"Your estimated gross profit for today is ₹{summary.estimated_gross_profit:,.2f}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"profit": float(summary.estimated_gross_profit)}
            )

        elif parsed.intent == IntentType.GET_EXPENSE_SUMMARY:
            summary = DashboardService.get_summary(db, business.id)
            if effective_lang == "kn":
                resp_text = f"ಇವತ್ತಿನ ಒಟ್ಟು ಖರ್ಚು ₹{summary.today_expenses:,.2f} ಆಗಿದೆ."
            elif effective_lang == "ml":
                resp_text = f"ഇന്നത്തെ ആകെ ചെലവ് ₹{summary.today_expenses:,.2f} ആണ്."
            elif effective_lang == "hi":
                resp_text = f"आज के दर्ज किए गए कुल खर्चे ₹{summary.today_expenses:,.2f} हैं।"
            elif effective_lang == "ta":
                resp_text = f"இன்றைய பதிவு செய்யப்பட்ட வணிகச் செலவுகள் ₹{summary.today_expenses:,.2f}."
            else:
                resp_text = f"Today's recorded business expenses are ₹{summary.today_expenses:,.2f}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"expenses": float(summary.today_expenses)}
            )

        elif parsed.intent == IntentType.GET_LOW_STOCK:
            low_stocks = DashboardService.get_low_stock_products(db, business.id, limit=5)
            if not low_stocks:
                if effective_lang == "kn":
                    resp_text = "ಎಲ್ಲಾ ವಸ್ತುಗಳ ಸ್ಟಾಕ್ ಸಮರ್ಪಕವಾಗಿದೆ. ಯಾವುದೇ ವಸ್ತು ಕಡಿಮೆ ಇಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = "എല്ലാ ഉൽപ്പന്നങ്ങളുടെയും സ്റ്റോക്ക് ആവശ്യത്തിനുണ്ട്."
                elif effective_lang == "hi":
                    resp_text = "सभी उत्पादों का स्टॉक पर्याप्त है। कोई उत्पाद कम नहीं है।"
                elif effective_lang == "ta":
                    resp_text = "அனைத்து பொருட்களும் போதுமான அளவு இருப்பு உள்ளன."
                else:
                    resp_text = "Great news! All products have healthy stock levels."
            else:
                names = ", ".join([f"{p.product_name} ({p.current_stock} {p.unit})" for p in low_stocks])
                if effective_lang == "kn":
                    resp_text = f"ಕಡಿಮೆ ಸ್ಟಾಕ್ ಇರುವ ಸರಕುಗಳು: {names}."
                elif effective_lang == "ml":
                    resp_text = f"സ്റ്റോക്ക് കുറവുള്ള ഉൽപ്പന്നങ്ങൾ: {names}."
                elif effective_lang == "hi":
                    resp_text = f"कम स्टॉक वाले आइटम: {names}."
                elif effective_lang == "ta":
                    resp_text = f"குறைந்த இருப்பு உள்ள பொருட்கள்: {names}."
                else:
                    resp_text = f"Products running low on stock: {names}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"low_stock_items": [p.product_name for p in low_stocks]}
            )

        elif parsed.intent == IntentType.GET_SALES_SUMMARY:
            resp_text = DashboardService.generate_daily_summary_text(db, business.id, lang=effective_lang)
            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64
            )

        elif parsed.intent == IntentType.GET_TOP_PRODUCTS:
            top_prods = DashboardService.get_top_products(db, business.id, limit=3)
            if not top_prods:
                if effective_lang == "kn":
                    resp_text = "ಇನ್ನೂ ಯಾವುದೇ ಮಾರಾಟ ದಾಖಲಾಗಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = "വിൽപ്പന വിവരങ്ങൾ ലഭ്യമല്ല."
                elif effective_lang == "hi":
                    resp_text = "अभी तक कोई बिक्री रिकॉर्ड नहीं हुई है।"
                elif effective_lang == "ta":
                    resp_text = "விற்பனை விவரங்கள் எதுவும் பதிவாகவில்லை."
                else:
                    resp_text = "No sales recorded yet."
            else:
                names = ", ".join([f"{p.product_name} ({p.quantity_sold} sold, ₹{p.revenue:,.2f})" for p in top_prods])
                if effective_lang == "kn":
                    resp_text = f"ಹೆಚ್ಚು ಮಾರಾಟವಾದ ಸರಕುಗಳು: {names}."
                elif effective_lang == "ml":
                    resp_text = f"ഏറ്റവും കൂടുതൽ വിറ്റഴിഞ്ഞ ഉൽപ്പന്നങ്ങൾ: {names}."
                elif effective_lang == "hi":
                    resp_text = f"सबसे अधिक बिकने वाले उत्पाद: {names}."
                elif effective_lang == "ta":
                    resp_text = f"அதிகமாக விற்பனையான பொருட்கள்: {names}."
                else:
                    resp_text = f"Your top selling products are: {names}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"top_products": [p.product_name for p in top_prods]}
            )

        elif parsed.intent == IntentType.GET_INVENTORY:
            prods = ProductService.get_products(db, business.id, limit=6)
            if not prods:
                if effective_lang == "kn":
                    resp_text = "ನಿಮ್ಮಲ್ಲಿ ಯಾವುದೇ ಉತ್ಪನ್ನಗಳು ನೋಂದಣಿಯಾಗಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = "ഉൽപ്പന്നങ്ങൾ ഒന്നും രേഖപ്പെടുത്തിയിട്ടില്ല."
                elif effective_lang == "hi":
                    resp_text = "आपकी सूची में कोई उत्पाद नहीं है।"
                elif effective_lang == "ta":
                    resp_text = "சரக்கு பட்டியலில் எந்த பொருட்களும் இல்லை."
                else:
                    resp_text = "No products found in your inventory."
            else:
                names = ", ".join([f"{p.product_name} ({p.current_stock} {p.unit})" for p in prods])
                if effective_lang == "kn":
                    resp_text = f"ದಾಸ್ತಾನು ವಿವರ: {names}."
                elif effective_lang == "ml":
                    resp_text = f"സ്റ്റോക്ക് വിവരം: {names}."
                elif effective_lang == "hi":
                    resp_text = f"स्टॉक का विवरण: {names}."
                elif effective_lang == "ta":
                    resp_text = f"சரக்கு இருப்பு விவரம்: {names}."
                else:
                    resp_text = f"Current inventory levels: {names}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"inventory_count": len(prods)}
            )

        elif parsed.intent == IntentType.GET_CUSTOMER_BALANCE:
            if not parsed.customer_name:
                resp_text = "Which customer's balance would you like to check?"
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )
            cust = CustomerService.get_customer_by_name(db, business.id, parsed.customer_name)
            if not cust:
                if effective_lang == "kn":
                    resp_text = f"ಗ್ರಾಹಕ '{parsed.customer_name}' ನಿಮ್ಮ ಲೆಡ್ಜರ್‌ನಲ್ಲಿ ಕಂಡುಬಂದಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = f"ഉപഭോക്താവ് '{parsed.customer_name}' നിങ്ങളുടെ ലെഡ്ജറിൽ കണ്ടെത്തിയില്ല."
                elif effective_lang == "hi":
                    resp_text = f"ग्राहक '{parsed.customer_name}' आपके खाते में नहीं मिले।"
                elif effective_lang == "ta":
                    resp_text = f"வாடிக்கையாளர் '{parsed.customer_name}' உங்கள் பதிவேட்டில் காணப்படவில்லை."
                else:
                    resp_text = f"I could not find a customer named '{parsed.customer_name}'."
            else:
                if effective_lang == "kn":
                    resp_text = f"{cust.customer_name} ಅವರ ಬಾಕಿ ಹಣ ₹{cust.outstanding_balance:,.2f} ಆಗಿದೆ."
                elif effective_lang == "ml":
                    resp_text = f"{cust.customer_name} നൽകാനുള്ള തുക ₹{cust.outstanding_balance:,.2f} ആണ്."
                elif effective_lang == "hi":
                    resp_text = f"{cust.customer_name} का कुल बकाया ₹{cust.outstanding_balance:,.2f} है।"
                elif effective_lang == "ta":
                    resp_text = f"{cust.customer_name} அவர்களின் நிலுவை கடன் ₹{cust.outstanding_balance:,.2f}."
                else:
                    resp_text = f"{cust.customer_name} owes ₹{cust.outstanding_balance:,.2f}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64
            )

        elif parsed.intent == IntentType.GET_TOP_PRODUCTS:
            top_prods = DashboardService.get_top_products(db, business.id, limit=3)
            if not top_prods:
                if effective_lang == "kn":
                    resp_text = "ಇನ್ನೂ ಯಾವುದೇ ಮಾರಾಟ ದಾಖಲಾಗಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = "വിൽപ്പന വിവരങ്ങൾ ലഭ്യമല്ല."
                elif effective_lang == "hi":
                    resp_text = "अभी तक कोई बिक्री रिकॉर्ड नहीं हुई है।"
                elif effective_lang == "ta":
                    resp_text = "விற்பனை விவரங்கள் எதுவும் பதிவாகவில்லை."
                else:
                    resp_text = "No sales recorded yet."
            else:
                names = ", ".join([f"{p.product_name} ({p.quantity_sold} sold, ₹{p.revenue:,.2f})" for p in top_prods])
                if effective_lang == "kn":
                    resp_text = f"ಹೆಚ್ಚು ಮಾರಾಟವಾದ ಸರಕುಗಳು: {names}."
                elif effective_lang == "ml":
                    resp_text = f"ഏറ്റവും കൂടുതൽ വിറ്റഴിഞ്ഞ ഉൽപ്പന്നങ്ങൾ: {names}."
                elif effective_lang == "hi":
                    resp_text = f"सबसे अधिक बिकने वाले उत्पाद: {names}."
                elif effective_lang == "ta":
                    resp_text = f"அதிகமாக விற்பனையான பொருட்கள்: {names}."
                else:
                    resp_text = f"Your top selling products are: {names}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"top_products": [p.product_name for p in top_prods]}
            )

        elif parsed.intent == IntentType.GET_INVENTORY:
            prods = ProductService.get_products(db, business.id, limit=6)
            if not prods:
                if effective_lang == "kn":
                    resp_text = "ನಿಮ್ಮಲ್ಲಿ ಯಾವುದೇ ಉತ್ಪನ್ನಗಳು ನೋಂದಣಿಯಾಗಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = "ഉൽപ്പന്നങ്ങൾ ഒന്നും രേഖപ്പെടുത്തിയിട്ടില്ല."
                elif effective_lang == "hi":
                    resp_text = "आपकी सूची में कोई उत्पाद नहीं है।"
                elif effective_lang == "ta":
                    resp_text = "சரக்கு பட்டியலில் எந்த பொருட்களும் இல்லை."
                else:
                    resp_text = "No products found in your inventory."
            else:
                names = ", ".join([f"{p.product_name} ({p.current_stock} {p.unit})" for p in prods])
                if effective_lang == "kn":
                    resp_text = f"ದಾಸ್ತಾನು ವಿವರ: {names}."
                elif effective_lang == "ml":
                    resp_text = f"സ്റ്റോക്ക് വിവരം: {names}."
                elif effective_lang == "hi":
                    resp_text = f"स्टॉक का विवरण: {names}."
                elif effective_lang == "ta":
                    resp_text = f"சரக்கு இருப்பு விவரம்: {names}."
                else:
                    resp_text = f"Current inventory levels: {names}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"inventory_count": len(prods)}
            )

        # WRITE ACTIONS — REQUIRE CONFIRMATION
        if parsed.intent == IntentType.UPDATE_STOCK:
            if not parsed.product_name or not parsed.quantity:
                resp_text = "Please specify the product and quantity to update stock."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )
            
            prod = ProductService.find_product_by_name_or_synonym(db, business.id, parsed.product_name)

            if not prod:
                if effective_lang == "kn":
                    resp_text = f"ನನಗೆ '{parsed.product_name}' ಉತ್ಪನ್ನ ಸಿಗಲಿಲ್ಲ. ನೀವು ಮೊದಲು ಅದನ್ನು ಸೇರಿಸಲು ಬಯಸುತ್ತೀರಾ?"
                elif effective_lang == "ml":
                    resp_text = f"'{parsed.product_name}' എന്ന ഉൽപ്പന്നം കണ്ടെത്താൻ കഴിഞ്ഞില്ല. ഇത് ആദ്യം ചേർക്കാൻ താൽപ്പര്യമുണ്ടോ?"
                elif effective_lang == "hi":
                    resp_text = f"मुझे '{parsed.product_name}' उत्पाद नहीं मिला। क्या आप इसे पहले जोड़ना चाहते हैं?"
                elif effective_lang == "ta":
                    resp_text = f"'{parsed.product_name}' என்ற பொருள் கிடைக்கவில்லை. இதை முதலில் சேர்க்க விரும்புகிறீர்களா?"
                else:
                    resp_text = f"I could not find the product '{parsed.product_name}'. Would you like to create it first?"

                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="FAILED",
                    response_text=resp_text
                )

            summary = f"Add {parsed.quantity} {prod.unit} to {prod.product_name} (Current: {prod.current_stock} {prod.unit})"
            if effective_lang == "kn":
                confirm_prompt = f"ನೀವು {prod.product_name} ಗೆ {parsed.quantity} {prod.unit} ಸ್ಟಾಕ್ ಸೇರಿಸಲು ಬಯಸಿದ್ದೀರಾ? ಖಚಿತಪಡಿಸಿ."
            elif effective_lang == "ml":
                confirm_prompt = f"{prod.product_name} എന്നതിൽ {parsed.quantity} {prod.unit} സ്റ്റോക്ക് ചേർക്കണോ? സ്ഥിരീകരിക്കുക."
            elif effective_lang == "hi":
                confirm_prompt = f"क्या आप {prod.product_name} में {parsed.quantity} {prod.unit} स्टॉक जोड़ना चाहते हैं? कृपया पुष्टि करें।"
            elif effective_lang == "ta":
                confirm_prompt = f"{prod.product_name} இல் {parsed.quantity} {prod.unit} சரக்கு சேர்க்க விரும்புகிறீர்களா? உறுதிப்படுத்தவும்."
            else:
                confirm_prompt = f"You want to add {parsed.quantity} {prod.unit} of {prod.product_name}. Should I update the stock?"

            token, details = VoiceOrchestrator._create_confirmation(
                business_id=business.id,
                user_id=user.id,
                action_type="UPDATE_STOCK",
                summary=summary,
                params={
                    "product_id": str(prod.id),
                    "product_name": prod.product_name,
                    "quantity": float(parsed.quantity),
                    "unit": prod.unit
                },
                lang=effective_lang
            )

            audio_b64 = await GnaniService.synthesize_speech(confirm_prompt, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "PENDING_CONFIRMATION", confirm_prompt)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="PENDING_CONFIRMATION",
                response_text=confirm_prompt,
                audio_base64=audio_b64,
                confirmation_token=token,
                pending_action=details
            )

        elif parsed.intent == IntentType.CREATE_SALE:
            if not parsed.product_name or not parsed.quantity:
                resp_text = "Please specify the item and quantity to record a sale."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )

            prod = ProductService.find_product_by_name_or_synonym(db, business.id, parsed.product_name)

            if not prod:
                if effective_lang == "kn":
                    resp_text = f"ಉತ್ಪನ್ನ '{parsed.product_name}' ನಿಮ್ಮ ದಾಸ್ತಾನಿನಲ್ಲಿ ಕಂಡುಬಂದಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = f"'{parsed.product_name}' എന്ന ഉൽപ്പന്നം നിങ്ങളുടെ സ്റ്റോക്കിൽ കണ്ടെത്തിയില്ല."
                elif effective_lang == "hi":
                    resp_text = f"उत्पाद '{parsed.product_name}' आपकी इन्वेंटरी में नहीं मिला।"
                elif effective_lang == "ta":
                    resp_text = f"'{parsed.product_name}' என்ற பொருள் உங்கள் சரக்கு இருப்பில் காணப்படவில்லை."
                else:
                    resp_text = f"Product '{parsed.product_name}' was not found in your inventory."

                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="FAILED",
                    response_text=resp_text
                )

            price = parsed.price if parsed.price is not None else (prod.selling_price * parsed.quantity)
            summary = f"Sell {parsed.quantity} {prod.unit} of {prod.product_name} for ₹{price:,.2f}"

            if effective_lang == "kn":
                confirm_prompt = f"{parsed.quantity} {prod.unit} {prod.product_name} ₹{price:,.2f} ಗೆ ಮಾರಾಟ ದಾಖಲಿಸಬೇಕೇ? ಖಚಿತಪಡಿಸಿ."
            elif effective_lang == "ml":
                confirm_prompt = f"{parsed.quantity} {prod.unit} {prod.product_name} ₹{price:,.2f} ന് വിൽക്കാൻ ഉറപ്പാണോ?"
            elif effective_lang == "hi":
                confirm_prompt = f"क्या आप ₹{price:,.2f} में {parsed.quantity} {prod.unit} {prod.product_name} की बिक्री दर्ज करना चाहते हैं?"
            elif effective_lang == "ta":
                confirm_prompt = f"{parsed.quantity} {prod.unit} {prod.product_name} ஐ ₹{price:,.2f} க்கு விற்பனை பதிவு செய்யவா? உறுதிப்படுத்தவும்."
            else:
                confirm_prompt = f"Record sale of {parsed.quantity} {prod.unit} {prod.product_name} for ₹{price:,.2f}. Should I confirm?"

            token, details = VoiceOrchestrator._create_confirmation(
                business_id=business.id,
                user_id=user.id,
                action_type="CREATE_SALE",
                summary=summary,
                params={
                    "product_id": str(prod.id),
                    "product_name": prod.product_name,
                    "quantity": float(parsed.quantity),
                    "price": float(price),
                    "unit": prod.unit
                },
                lang=effective_lang
            )

            audio_b64 = await GnaniService.synthesize_speech(confirm_prompt, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "PENDING_CONFIRMATION", confirm_prompt)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="PENDING_CONFIRMATION",
                response_text=confirm_prompt,
                audio_base64=audio_b64,
                confirmation_token=token,
                pending_action=details
            )

        elif parsed.intent == IntentType.RECORD_REPAYMENT:
            if not parsed.customer_name or not parsed.amount:
                resp_text = "Please specify customer name and payment amount."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )

            cust = CustomerService.get_customer_by_name(db, business.id, parsed.customer_name)
            if not cust:
                if effective_lang == "kn":
                    resp_text = f"ಗ್ರಾಹಕ '{parsed.customer_name}' ನಿಮ್ಮ ಲೆಡ್ಜರ್‌ನಲ್ಲಿ ಕಂಡುಬಂದಿಲ್ಲ."
                elif effective_lang == "ml":
                    resp_text = f"ഉപഭോക്താവ് '{parsed.customer_name}' നിങ്ങളുടെ ലെഡ്ജറിൽ കണ്ടെത്തിയില്ല."
                elif effective_lang == "hi":
                    resp_text = f"ग्राहक '{parsed.customer_name}' आपके खाते में नहीं मिले।"
                elif effective_lang == "ta":
                    resp_text = f"வாடிக்கையாளர் '{parsed.customer_name}' உங்கள் பதிவேட்டில் காணப்படவில்லை."
                else:
                    resp_text = f"Customer '{parsed.customer_name}' was not found in your ledger."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="FAILED",
                    response_text=resp_text
                )

            summary = f"Record repayment of ₹{parsed.amount:,.2f} from {cust.customer_name}"
            if effective_lang == "kn":
                confirm_prompt = f"{cust.customer_name} ಅವರಿಂದ ₹{parsed.amount:,.2f} ಮರುಪಾವತಿ ದಾಖಲಿಸಬೇಕೇ?"
            elif effective_lang == "ml":
                confirm_prompt = f"{cust.customer_name} ൽ നിന്ന് ₹{parsed.amount:,.2f} തിരിച്ചടവ് രേഖപ്പെടുത്തണോ?"
            elif effective_lang == "hi":
                confirm_prompt = f"क्या {cust.customer_name} से ₹{parsed.amount:,.2f} का भुगतान दर्ज करें?"
            elif effective_lang == "ta":
                confirm_prompt = f"{cust.customer_name} இடமிருந்து ₹{parsed.amount:,.2f} திரும்ப கட்டுதல் பதிவு செய்யவா?"
            else:
                confirm_prompt = f"Record repayment of ₹{parsed.amount:,.2f} from {cust.customer_name}?"

            token, details = VoiceOrchestrator._create_confirmation(
                business_id=business.id,
                user_id=user.id,
                action_type="RECORD_REPAYMENT",
                summary=summary,
                params={
                    "customer_id": str(cust.id),
                    "customer_name": cust.customer_name,
                    "amount": float(parsed.amount)
                },
                lang=effective_lang
            )

            audio_b64 = await GnaniService.synthesize_speech(confirm_prompt, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "PENDING_CONFIRMATION", confirm_prompt)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="PENDING_CONFIRMATION",
                response_text=confirm_prompt,
                audio_base64=audio_b64,
                confirmation_token=token,
                pending_action=details
            )

        elif parsed.intent == IntentType.ADD_EXPENSE:
            if not parsed.amount:
                resp_text = "Please specify the expense amount."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )

            summary = f"Add expense of ₹{parsed.amount:,.2f} for {parsed.expense_category or 'General'}"
            if effective_lang == "kn":
                confirm_prompt = f"₹{parsed.amount:,.2f} ಖರ್ಚನ್ನು {parsed.expense_category or 'ಇತರೆ'} ವರ್ಗದಲ್ಲಿ ಸೇರಿಸಬೇಕೇ?"
            elif effective_lang == "ml":
                confirm_prompt = f"₹{parsed.amount:,.2f} ചെലവ് രേഖപ്പെടുത്തണോ?"
            elif effective_lang == "hi":
                confirm_prompt = f"क्या ₹{parsed.amount:,.2f} का खर्च जोड़ें?"
            elif effective_lang == "ta":
                confirm_prompt = f"₹{parsed.amount:,.2f} செலவை {parsed.expense_category or 'பொதுவான'} பிரிவில் சேர்க்கவா?"
            else:
                confirm_prompt = f"Record expense of ₹{parsed.amount:,.2f} for {parsed.expense_category or 'General'}?"

            token, details = VoiceOrchestrator._create_confirmation(
                business_id=business.id,
                user_id=user.id,
                action_type="ADD_EXPENSE",
                summary=summary,
                params={
                    "amount": float(parsed.amount),
                    "category": parsed.expense_category or "Miscellaneous",
                    "description": parsed.description or "Voice recorded expense"
                },
                lang=effective_lang
            )

            audio_b64 = await GnaniService.synthesize_speech(confirm_prompt, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "PENDING_CONFIRMATION", confirm_prompt)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="PENDING_CONFIRMATION",
                response_text=confirm_prompt,
                audio_base64=audio_b64,
                confirmation_token=token,
                pending_action=details
            )

        elif parsed.intent == IntentType.CREATE_CREDIT:
            if not parsed.customer_name or not parsed.amount:
                resp_text = "Please specify customer name and credit amount."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )

            cust = CustomerService.get_customer_by_name(db, business.id, parsed.customer_name)
            if not cust:
                if effective_lang == "kn":
                    resp_text = f"ಗ್ರಾಹಕ '{parsed.customer_name}' ನಿಮ್ಮ ಲೆಡ್ಜರ್‌ನಲ್ಲಿ ಕಂಡುಬಂದಿಲ್ಲ. ನೀವು ಮೊದಲು ಅವರನ್ನು ಸೇರಿಸಲು ಬಯಸುತ್ತೀರಾ?"
                elif effective_lang == "ml":
                    resp_text = f"ഉപഭോക്താവ് '{parsed.customer_name}' നിങ്ങളുടെ ലെഡ്ജറിൽ കണ്ടെത്തിയില്ല. അവരെ ആദ്യം ചേർക്കണോ?"
                elif effective_lang == "hi":
                    resp_text = f"ग्राहक '{parsed.customer_name}' आपके खाते में नहीं मिले। क्या आप पहले उन्हें जोड़ना चाहते हैं?"
                elif effective_lang == "ta":
                    resp_text = f"வாடிக்கையாளர் '{parsed.customer_name}' உங்கள் பதிவேட்டில் காணப்படவில்லை. முதலில் சேர்க்கவா?"
                else:
                    resp_text = f"Customer '{parsed.customer_name}' was not found in your ledger. Would you like to add them first?"
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="FAILED",
                    response_text=resp_text
                )

            summary = f"Give ₹{parsed.amount:,.2f} credit to {cust.customer_name}"
            if effective_lang == "kn":
                confirm_prompt = f"{cust.customer_name} ಅವರಿಗೆ ₹{parsed.amount:,.2f} ಸಾಲ ನೀಡಬೇಕೇ? ಖಚಿತಪಡಿಸಿ."
            elif effective_lang == "ml":
                confirm_prompt = f"{cust.customer_name} ന് ₹{parsed.amount:,.2f} കടം നൽകണോ? സ്ഥിരീകരിക്കുക."
            elif effective_lang == "hi":
                confirm_prompt = f"क्या {cust.customer_name} को ₹{parsed.amount:,.2f} का उधार दें? कृपया पुष्टि करें।"
            elif effective_lang == "ta":
                confirm_prompt = f"{cust.customer_name} அவர்களுக்கு ₹{parsed.amount:,.2f} கடன் கொடுக்கவா? உறுதிப்படுத்தவும்."
            else:
                confirm_prompt = f"Give ₹{parsed.amount:,.2f} credit to {cust.customer_name}. Should I confirm?"

            token, details = VoiceOrchestrator._create_confirmation(
                business_id=business.id,
                user_id=user.id,
                action_type="CREATE_CREDIT",
                summary=summary,
                params={
                    "customer_id": str(cust.id),
                    "customer_name": cust.customer_name,
                    "amount": float(parsed.amount)
                },
                lang=effective_lang
            )

            audio_b64 = await GnaniService.synthesize_speech(confirm_prompt, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "PENDING_CONFIRMATION", confirm_prompt)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="PENDING_CONFIRMATION",
                response_text=confirm_prompt,
                audio_base64=audio_b64,
                confirmation_token=token,
                pending_action=details
            )

        elif parsed.intent == IntentType.ADD_CUSTOMER:
            if not parsed.customer_name:
                resp_text = "Please specify the customer name to add."
                return VoiceCommandResponse(
                    transcription=transcription,
                    detected_language=effective_lang,
                    parsed_intent=parsed,
                    execution_status="CLARIFICATION_NEEDED",
                    response_text=resp_text
                )

            summary = f"Add new customer {parsed.customer_name}" + (f" ({parsed.customer_phone})" if parsed.customer_phone else "")
            if effective_lang == "kn":
                confirm_prompt = f"ಹೊಸ ಗ್ರಾಹಕ {parsed.customer_name} ಅವರನ್ನು ಸೇರಿಸಬೇಕೇ? ಖಚಿತಪಡಿಸಿ."
            elif effective_lang == "ml":
                confirm_prompt = f"പുതിയ ഉപഭോക്താവ് {parsed.customer_name} എന്നയാളെ ചേർക്കണോ?"
            elif effective_lang == "hi":
                confirm_prompt = f"क्या नए ग्राहक {parsed.customer_name} को जोड़ें? कृपया पुष्टि करें।"
            elif effective_lang == "ta":
                confirm_prompt = f"புதிய வாடிக்கையாளர் {parsed.customer_name} அவர்களை சேர்க்கவா? உறுதிப்படுத்தவும்."
            else:
                confirm_prompt = f"Add new customer {parsed.customer_name}. Should I confirm?"

            token, details = VoiceOrchestrator._create_confirmation(
                business_id=business.id,
                user_id=user.id,
                action_type="ADD_CUSTOMER",
                summary=summary,
                params={
                    "customer_name": parsed.customer_name,
                    "phone": parsed.customer_phone
                },
                lang=effective_lang
            )

            audio_b64 = await GnaniService.synthesize_speech(confirm_prompt, language=effective_lang)
            VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "PENDING_CONFIRMATION", confirm_prompt)

            return VoiceCommandResponse(
                transcription=transcription,
                detected_language=effective_lang,
                parsed_intent=parsed,
                execution_status="PENDING_CONFIRMATION",
                response_text=confirm_prompt,
                audio_base64=audio_b64,
                confirmation_token=token,
                pending_action=details
            )

        # UNKNOWN OR FALLBACK
        if effective_lang == "kn":
            resp_text = parsed.clarification_question or "ಕ್ಷಮಿಸಿ, ಆ ವಿನಂತಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ."
        elif effective_lang == "ml":
            resp_text = parsed.clarification_question or "ക്ഷമിക്കണം, ആ അഭ്യർത്ഥന പ്രോസസ്സ് ചെയ്യാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക."
        elif effective_lang == "hi":
            resp_text = parsed.clarification_question or "क्षमा करें, मैं उस अनुरोध को संसाधित नहीं कर सका। कृपया पुनः प्रयास करें।"
        elif effective_lang == "ta":
            resp_text = parsed.clarification_question or "மன்னிக்கவும், அந்த கோரிக்கையை செயல்படுத்த முடியவில்லை. மீண்டும் முயற்சிக்கவும்."
        else:
            resp_text = parsed.clarification_question or "I could not process that request. Please try again."
        audio_b64 = await GnaniService.synthesize_speech(resp_text, language=effective_lang)
        VoiceOrchestrator._log_interaction(db, business.id, user.id, effective_lang, transcription, parsed.intent.value, "FAILED", resp_text)

        return VoiceCommandResponse(
            transcription=transcription,
            detected_language=effective_lang,
            parsed_intent=parsed,
            execution_status="FAILED",
            response_text=resp_text,
            audio_base64=audio_b64
        )

    @staticmethod
    async def confirm_action(
        db: Session,
        token: str,
        confirmed: bool,
        current_user_id: Optional[uuid.UUID] = None
    ) -> VoiceCommandResponse:
        if token not in _pending_actions:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confirmation token not found or expired")

        action_data = _pending_actions[token]
        if datetime.now(timezone.utc) > action_data["expires_at"]:
            _pending_actions.pop(token, None)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation token has expired")

        if current_user_id and action_data["user_id"] != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to confirm this action")

        _pending_actions.pop(token, None)

        lang = action_data["lang"]
        action_type = action_data["action_type"]
        params = action_data["params"]
        b_id = action_data["business_id"]
        u_id = action_data["user_id"]

        if not confirmed:
            if lang == "kn":
                resp_text = "ಕ್ರಿಯೆಯನ್ನು ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ."
            elif lang == "ml":
                resp_text = "പ്രവർത്തനം റദ്ദാക്കി."
            elif lang == "hi":
                resp_text = "कार्रवाई रद्द कर दी गई है।"
            elif lang == "ta":
                resp_text = "செயல் ரத்து செய்யப்பட்டது."
            else:
                resp_text = "Action cancelled."
            
            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            return VoiceCommandResponse(
                transcription="",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.UNKNOWN_INTENT, language=lang),
                execution_status="CANCELLED",
                response_text=resp_text,
                audio_base64=audio_b64
            )

        # EXECUTE CONFIRMED ACTION
        if action_type == "UPDATE_STOCK":
            p_id = uuid.UUID(params["product_id"])
            qty = Decimal(str(params["quantity"]))
            prod = ProductService.adjust_stock(
                db, b_id,
                InventoryAdjustment(
                    product_id=p_id,
                    quantity_change=qty,
                    transaction_type="RESTOCK",
                    description="Voice confirmed stock update"
                )
            )
            if lang == "kn":
                resp_text = f"ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ. {prod.product_name} ಸ್ಟಾಕ್ ಈಗ {prod.current_stock} {prod.unit} ಇದೆ."
            elif lang == "ml":
                resp_text = f"വിജയകരമായി പുതുക്കി. {prod.product_name} ഇപ്പോൾ {prod.current_stock} {prod.unit} സ്റ്റോക്കുണ്ട്."
            elif lang == "hi":
                resp_text = f"सफलतापूर्वक अपडेट किया गया। {prod.product_name} का नया स्टॉक अब {prod.current_stock} {prod.unit} है।"
            elif lang == "ta":
                resp_text = f"வெற்றிகரமாக புதுப்பிக்கப்பட்டது. {prod.product_name} இருப்பு இப்போது {prod.current_stock} {prod.unit} உள்ளது."
            else:
                resp_text = f"Successfully updated. {prod.product_name} stock is now {prod.current_stock} {prod.unit}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            VoiceOrchestrator._log_interaction(db, b_id, u_id, lang, f"CONFIRM {action_type}", "UPDATE_STOCK", "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=f"Confirmed {action_data['summary']}",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.UPDATE_STOCK, language=lang),
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"new_stock": float(prod.current_stock), "product_name": prod.product_name}
            )

        elif action_type == "CREATE_SALE":
            p_id = uuid.UUID(params["product_id"])
            qty = Decimal(str(params["quantity"]))
            price = Decimal(str(params["price"]))
            
            sale = SalesService.create_sale(
                db, b_id,
                SaleCreate(
                    items=[SaleItemCreate(product_id=p_id, quantity=qty, unit_price=price / qty)],
                    payment_method="Cash"
                )
            )

            if lang == "kn":
                resp_text = f"ಮಾರಾಟ ಯಶಸ್ವಿಯಾಗಿ ದಾಖಲಾಗಿದೆ. ಇನ್‌ವಾಯ್ಸ್ ನಂಬರ್: {sale.invoice_number}, ಒಟ್ಟು: ₹{sale.total_amount:,.2f}."
            elif lang == "ml":
                resp_text = f"വിൽപ്പന രേഖപ്പെടുത്തി. ഇൻവോയ്സ്: {sale.invoice_number}, ആകെ തുക: ₹{sale.total_amount:,.2f}."
            elif lang == "hi":
                resp_text = f"बिक्री सफलतापूर्वक दर्ज की गई। बिल नंबर {sale.invoice_number}, कुल राशि ₹{sale.total_amount:,.2f}।"
            elif lang == "ta":
                resp_text = f"விற்பனை வெற்றிகரமாக பதிவானது. பில் எண்: {sale.invoice_number}, மொத்தம்: ₹{sale.total_amount:,.2f}."
            else:
                resp_text = f"Sale recorded successfully! Invoice {sale.invoice_number} for ₹{sale.total_amount:,.2f}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            VoiceOrchestrator._log_interaction(db, b_id, u_id, lang, f"CONFIRM {action_type}", "CREATE_SALE", "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=f"Confirmed {action_data['summary']}",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.CREATE_SALE, language=lang),
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"invoice_number": sale.invoice_number, "total_amount": float(sale.total_amount)}
            )

        elif action_type == "RECORD_REPAYMENT":
            c_id = uuid.UUID(params["customer_id"])
            amt = Decimal(str(params["amount"]))
            tx = CustomerService.record_repayment(
                db, b_id, c_id,
                RepaymentCreate(amount=amt, payment_method="Cash", description="Voice recorded repayment")
            )
            cust = CustomerService.get_customer_by_id(db, b_id, c_id)

            if lang == "kn":
                resp_text = f"ಮರುಪಾವತಿ ದಾಖಲಾಗಿದೆ. {cust.customer_name} ಅವರ ಇನ್ನುಳಿದ ಬಾಕಿ ₹{cust.outstanding_balance:,.2f}."
            elif lang == "ml":
                resp_text = f"തിരിച്ചടവ് രേഖപ്പെടുത്തി. {cust.customer_name} ഇനി ബാക്കി നൽകാനുള്ളത് ₹{cust.outstanding_balance:,.2f}."
            elif lang == "hi":
                resp_text = f"भुगतान दर्ज कर लिया गया है। {cust.customer_name} का शेष बकाया ₹{cust.outstanding_balance:,.2f} है।"
            elif lang == "ta":
                resp_text = f"திரும்ப செலுத்துதல் பதிவானது. {cust.customer_name} அவர்களின் மீதி நிலுவை ₹{cust.outstanding_balance:,.2f}."
            else:
                resp_text = f"Repayment recorded! {cust.customer_name}'s remaining balance is ₹{cust.outstanding_balance:,.2f}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            VoiceOrchestrator._log_interaction(db, b_id, u_id, lang, f"CONFIRM {action_type}", "RECORD_REPAYMENT", "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=f"Confirmed {action_data['summary']}",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.RECORD_REPAYMENT, language=lang),
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"remaining_balance": float(cust.outstanding_balance)}
            )

        elif action_type == "ADD_EXPENSE":
            amt = Decimal(str(params["amount"]))
            cat = params["category"]
            exp = ExpenseService.create_expense(
                db, b_id,
                ExpenseCreate(
                    amount=amt,
                    category=cat,
                    description=params["description"]
                )
            )

            if lang == "kn":
                resp_text = f"₹{exp.amount:,.2f} ಖರ್ಚನ್ನು {exp.category} ವರ್ಗಕ್ಕೆ ಸೇರಿಸಲಾಗಿದೆ."
            elif lang == "ml":
                resp_text = f"₹{exp.amount:,.2f} ചെലവ് രേഖപ്പെടുത്തി."
            elif lang == "hi":
                resp_text = f"₹{exp.amount:,.2f} का खर्च {exp.category} श्रेणी में दर्ज कर लिया गया है।"
            elif lang == "ta":
                resp_text = f"₹{exp.amount:,.2f} செலவு {exp.category} பிரிவில் சேர்க்கப்பட்டது."
            else:
                resp_text = f"Recorded expense of ₹{exp.amount:,.2f} under {exp.category}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            VoiceOrchestrator._log_interaction(db, b_id, u_id, lang, f"CONFIRM {action_type}", "ADD_EXPENSE", "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=f"Confirmed {action_data['summary']}",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.ADD_EXPENSE, language=lang),
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"expense_id": str(exp.id), "amount": float(exp.amount)}
            )

        elif action_type == "CREATE_CREDIT":
            c_id = uuid.UUID(params["customer_id"])
            amt = Decimal(str(params["amount"]))
            tx = CustomerService.record_credit(
                db, b_id, c_id, amt,
                description="Voice confirmed credit entry"
            )
            cust = CustomerService.get_customer_by_id(db, b_id, c_id)

            if lang == "kn":
                resp_text = f"ಸಾಲ ದಾಖಲಾಗಿದೆ. {cust.customer_name} ಅವರ ಒಟ್ಟು ಬಾಕಿ ಈಗ ₹{cust.outstanding_balance:,.2f}."
            elif lang == "ml":
                resp_text = f"കടം രേഖപ്പെടുത്തി. {cust.customer_name} ഇനി നൽകാനുള്ള തുക ₹{cust.outstanding_balance:,.2f}."
            elif lang == "hi":
                resp_text = f"उधार दर्ज कर लिया गया है। {cust.customer_name} का कुल बकाया अब ₹{cust.outstanding_balance:,.2f} है।"
            elif lang == "ta":
                resp_text = f"கடன் பதிவானது. {cust.customer_name} அவர்களின் மொத்த நிலுவை கடன் இப்போது ₹{cust.outstanding_balance:,.2f}."
            else:
                resp_text = f"Credit recorded! {cust.customer_name}'s total balance is now ₹{cust.outstanding_balance:,.2f}."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            VoiceOrchestrator._log_interaction(db, b_id, u_id, lang, f"CONFIRM {action_type}", "CREATE_CREDIT", "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=f"Confirmed {action_data['summary']}",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.CREATE_CREDIT, language=lang),
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"customer_id": str(cust.id), "new_balance": float(cust.outstanding_balance)}
            )

        elif action_type == "ADD_CUSTOMER":
            c_name = params["customer_name"]
            phone = params.get("phone")
            new_cust = CustomerService.create_customer(
                db, b_id,
                CustomerCreate(customer_name=c_name, phone=phone, initial_balance=Decimal("0.00"))
            )

            if lang == "kn":
                resp_text = f"ಹೊಸ ಗ್ರಾಹಕ {new_cust.customer_name} ಯಶಸ್ವಿಯಾಗಿ ಸೇರಿಸಲಾಗಿದೆ."
            elif lang == "ml":
                resp_text = f"പുതിയ ഉപഭോക്താവ് {new_cust.customer_name} ചേർത്തു."
            elif lang == "hi":
                resp_text = f"नए ग्राहक {new_cust.customer_name} को सफलतापूर्वक जोड़ दिया गया है।"
            elif lang == "ta":
                resp_text = f"புதிய வாடிக்கையாளர் {new_cust.customer_name} வெற்றிகரமாக சேர்க்கப்பட்டார்."
            else:
                resp_text = f"New customer {new_cust.customer_name} added successfully."

            audio_b64 = await GnaniService.synthesize_speech(resp_text, language=lang)
            VoiceOrchestrator._log_interaction(db, b_id, u_id, lang, f"CONFIRM {action_type}", "ADD_CUSTOMER", "SUCCESS", resp_text)

            return VoiceCommandResponse(
                transcription=f"Confirmed {action_data['summary']}",
                detected_language=lang,
                parsed_intent=ParsedIntent(intent=IntentType.ADD_CUSTOMER, language=lang),
                execution_status="SUCCESS",
                response_text=resp_text,
                audio_base64=audio_b64,
                data={"customer_id": str(new_cust.id), "customer_name": new_cust.customer_name}
            )

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported action type")

    @staticmethod
    def _log_interaction(
        db: Session,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        lang: str,
        transcript: str,
        intent: str,
        status_str: str,
        resp_text: str
    ):
        try:
            interaction = VoiceInteraction(
                business_id=business_id,
                user_id=user_id,
                input_language=lang,
                transcription=transcript,
                detected_intent=intent,
                execution_status=status_str,
                response_text=resp_text
            )
            db.add(interaction)
            db.commit()
        except Exception:
            db.rollback()

