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
        parsed = IntentService.parse_text(transcription, user_lang=user.preferred_language)
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
                resp_text = f"I could not find a customer named '{parsed.customer_name}'."
            else:
                if effective_lang == "kn":
                    resp_text = f"{cust.customer_name} ಅವರ ಬಾಕಿ ಹಣ ₹{cust.outstanding_balance:,.2f} ಆಗಿದೆ."
                elif effective_lang == "ml":
                    resp_text = f"{cust.customer_name} നൽകാനുള്ള തുക ₹{cust.outstanding_balance:,.2f} ആണ്."
                elif effective_lang == "hi":
                    resp_text = f"{cust.customer_name} का कुल बकाया ₹{cust.outstanding_balance:,.2f} है।"
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
            
            prod = ProductService.get_product_by_name(db, business.id, parsed.product_name)
            if not prod:
                # Try finding closest or fuzzy match
                all_prods = ProductService.get_products(db, business.id, search=parsed.product_name)
                prod = all_prods[0] if all_prods else None

            if not prod:
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

            prod = ProductService.get_product_by_name(db, business.id, parsed.product_name)
            if not prod:
                all_prods = ProductService.get_products(db, business.id, search=parsed.product_name)
                prod = all_prods[0] if all_prods else None

            if not prod:
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

        # UNKNOWN OR FALLBACK
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
        confirmed: bool
    ) -> VoiceCommandResponse:
        if token not in _pending_actions:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confirmation token not found or expired")

        action_data = _pending_actions.pop(token)
        if datetime.now(timezone.utc) > action_data["expires_at"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation token has expired")

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
