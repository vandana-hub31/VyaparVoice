import re
from decimal import Decimal
from typing import Optional, Tuple
from app.schemas.intent import IntentType, ParsedIntent, IntentItem

class IntentService:
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect language from Unicode block ranges."""
        for char in text:
            # Tamil: 0x0B80 - 0x0BFF (must be before Malayalam since adjacent)
            if '\u0B80' <= char <= '\u0BFF':
                return "ta"
            # Kannada: 0x0C80 - 0x0CFF
            if '\u0C80' <= char <= '\u0CFF':
                return "kn"
            # Malayalam: 0x0D00 - 0x0D7F
            if '\u0D00' <= char <= '\u0D7F':
                return "ml"
            # Devanagari (Hindi): 0x0900 - 0x097F
            if '\u0900' <= char <= '\u097F':
                return "hi"
        return "en"

    @staticmethod
    def _extract_number(text: str) -> Optional[Decimal]:
        match = re.search(r'₹?\s*(\d+(?:\.\d+)?)', text)
        if match:
            try:
                return Decimal(match.group(1))
            except Exception:
                return None
        return None

    @staticmethod
    def parse_text(text: str, user_lang: Optional[str] = None) -> ParsedIntent:
        cleaned = text.strip()
        lower = cleaned.lower()
        detected_lang = IntentService.detect_language(cleaned)
        effective_lang = detected_lang if detected_lang != "en" else (user_lang or "en")

        # 1. GET_TODAYS_SALES
        if any(w in lower for w in [
            "today's sales", "todays sales", "sell today", "sales today", "how much did i sell", "today sale",
            "आज कितनी बिक्री", "आज की बिक्री", "आज कितना बिका", "इतना बिका",
            "ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್", "ಇವತ್ತಿನ ಮಾರಾಟ", "ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ", "ಇಂದಿನ ಮಾರಾಟ",
            "ഇന്ന് എത്ര രൂപയുടെ വിൽപ്പന", "ഇന്നത്തെ വിൽപ്പന", "എത്ര രൂപയുടെ വിൽപ്പന",
            "இன்று எவ்வளவு விற்றோம்", "இன்றைய விற்பனை", "இன்று விற்பனை"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_TODAYS_SALES,
                language=effective_lang,
                requires_confirmation=False,
                time_period="today"
            )

        # 2. GET_PROFIT_SUMMARY
        if any(w in lower for w in [
            "profit", "gross profit", "how much profit", "profit today",
            "मुनाफा", "लाभ", "कितना लाभ", "आज का मुनाफा",
            "ಲಾಭ", "ಎಷ್ಟು ಲಾಭ", "ಇವತ್ತು ಎಷ್ಟು ಲಾಭ",
            "ലാഭം", "എത്ര ലാഭം", "ഇന്ന് എത്ര ലാഭം",
            "லாபம்", "இன்றைய லாபம்"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_PROFIT_SUMMARY,
                language=effective_lang,
                requires_confirmation=False,
                time_period="today"
            )

        # 3. GET_EXPENSE_SUMMARY
        if any(w in lower for w in [
            "expense summary", "my expenses", "how much expense", "total expenses", "show expenses",
            "खर्चे", "कुल खर्च", "आज का खर्च",
            "ಖರ್ಚು", "ಇವತ್ತಿನ ಖರ್ಚು", "ಖರ್ಚುಗಳು",
            "ചെലവ്", "ഇന്നത്തെ ചെലവ്", "ആകെ ചെലവുകൾ",
            "செலவு", "இன்றைய செலவு"
        ]) and not any(w in lower for w in ["add expense", "जोड़ो", "ಸೇರಿಸಿ", "ചേർക്കുക", "செலவு சேர்"]):
            return ParsedIntent(
                intent=IntentType.GET_EXPENSE_SUMMARY,
                language=effective_lang,
                requires_confirmation=False,
                time_period="today"
            )

        # 4. GET_LOW_STOCK
        if any(w in lower for w in [
            "low stock", "low-stock", "running low", "shortage", "out of stock",
            "कम स्टॉक", "खत्म होने वाला",
            "ಕಡಿಮೆ ಸ್ಟಾಕ್", "ಸ್ಟಾಕ್ ಕಡಿಮೆ",
            "കുറഞ്ഞ സ്റ്റോക്ക്", "സ്റ്റോക്ക് കുറവ്",
            "குறைந்த சரக்கு", "சரக்கு குறைவு"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_LOW_STOCK,
                language=effective_lang,
                requires_confirmation=False
            )

        # 5. GET_TOP_PRODUCTS
        if any(w in lower for w in [
            "top product", "best selling", "top selling", "highest sales",
            "सबसे ज्यादा बिकने", "टॉप उत्पाद",
            "ಹೆಚ್ಚು ಮಾರಾಟ", "ಉತ್ತಮ ಉತ್ಪನ್ನ",
            "കൂടുതൽ വിറ്റഴിക്കപ്പെടുന്ന", "മികച്ച ഉൽപ്പന്നങ്ങൾ",
            "அதிக விற்பனையான", "சிறந்த தயாரிப்புகள்"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_TOP_PRODUCTS,
                language=effective_lang,
                requires_confirmation=False
            )

        # 6. GET_SALES_SUMMARY
        if any(w in lower for w in [
            "sales summary", "weekly sales", "monthly sales", "all sales",
            "बिक्री सारांश", "हफ्ते की बिक्री", "महीने की बिक्री",
            "ಮಾರಾಟ ಸಾರಾಂಶ", "ವಾರದ ಮಾರಾಟ",
            "വിൽപ്പന വിവരണം", "ആഴ്ചയിലെ വിൽപ്പന",
            "விற்பனை சுருக்கம்", "வார விற்பனை"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_SALES_SUMMARY,
                language=effective_lang,
                requires_confirmation=False
            )

        # 7. GET_INVENTORY
        if any(w in lower for w in [
            "show inventory", "inventory list", "all stock", "product stock", "stock of",
            "स्टॉक सूची", "इन्वेंट्री",
            "ಇನ್ವೆಂಟರಿ", "ದಾಸ್ತಾನು",
            "ഇൻവെന്ററി", "സ്റ്റോക്ക് വിവരം",
            "சரக்கு பட்டியல்", "இருப்பு விவரம்"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_INVENTORY,
                language=effective_lang,
                requires_confirmation=False
            )

        # 8. RECORD_REPAYMENT
        # e.g. "Ramesh paid 200", "Received 500 from Suresh", "रमेश ने 200 रुपये दिए", "ರಮೇಶ್ 200 ರೂಪಾಯಿ ಕೊಟ್ಟರು"
        repay_pattern = re.search(r'([A-Za-z\u0900-\u0D7F]+)\s+(?:paid|gives|gave|returned|ने|ಕೊಟ್ಟರು|തന്നു|கொடுத்தார்)\s*(?:₹|rs\.?|rupees|रुपये|ರೂಪಾಯಿ|രൂപ)?\s*(\d+(?:\.\d+)?)', cleaned, re.IGNORECASE)
        if repay_pattern or "repayment" in lower:
            cust_name = repay_pattern.group(1).strip() if repay_pattern else None
            amount = Decimal(repay_pattern.group(2)) if repay_pattern else None
            
            # Clean customer name if it caught prepositions
            if cust_name and cust_name.lower() in ["customer", "from", "ने"]:
                cust_name = None

            return ParsedIntent(
                intent=IntentType.RECORD_REPAYMENT,
                customer_name=cust_name,
                amount=amount,
                language=effective_lang,
                requires_confirmation=True
            )

        # 9. CREATE_CREDIT
        # e.g. "Ramesh owes me 500", "Give 300 credit to Suresh", "रमेश पर 500 रुपये उधार है"
        credit_pattern = re.search(r'([A-Za-z\u0900-\u0D7F]+)\s+(?:owes|borrowed|उधार|ಸಾಲ|കടം)\s*(?:me)?\s*(?:₹|rs\.?|rupees|रुपये|ರೂಪಾಯಿ|രൂപ)?\s*(\d+(?:\.\d+)?)', cleaned, re.IGNORECASE)
        if credit_pattern or "credit" in lower and any(w in lower for w in ["owes", "give", "to", "उधार", "ಸಾಲ"]):
            cust_name = credit_pattern.group(1).strip() if credit_pattern else None
            amount = Decimal(credit_pattern.group(2)) if credit_pattern else None
            return ParsedIntent(
                intent=IntentType.CREATE_CREDIT,
                customer_name=cust_name,
                amount=amount,
                language=effective_lang,
                requires_confirmation=True
            )

        # 10. GET_CUSTOMER_BALANCE
        # e.g. "How much does Ramesh owe?", "Ramesh balance", "रमेश का बकाया कितना है?"
        if any(w in lower for w in ["owe", "balance", "बकाया", "ಉಳಿಕೆ", "ಬಾಕಿ", "കുടിശ്ശിക", "கடன்"]) and not any(w in lower for w in ["paid", "repay"]):
            name_match = re.search(r'([A-Za-z\u0900-\u0D7F]+)(?:\s+(?:balance|owe|का बकाया|ಬಾಕಿ|കുടിശ്ശിക)|\'s balance)', cleaned, re.IGNORECASE)
            c_name = name_match.group(1).strip() if name_match else None
            return ParsedIntent(
                intent=IntentType.GET_CUSTOMER_BALANCE,
                customer_name=c_name,
                language=effective_lang,
                requires_confirmation=False
            )

        # 11. UPDATE_STOCK
        # e.g. "Add 10 packets of milk", "Add 5 milk packets", "10 पैकेट दूध जोड़ो", "10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸೇರಿಸಿ", "10 പാക്കറ്റ് പാൽ ചേർക്കുക"
        stock_match = re.search(
            r'(?:add|restock|जोड़ो|सೇರಿಸಿ|ചേർക്കുക)\s*(\d+(?:\.\d+)?)\s*(packets?|kg|g|l|litres?|pcs|पैक|ಪ್ಯಾಕೆಟ್|പാക്കറ്റ്)?\s*(?:of\s+)?([A-Za-z\u0900-\u0D7F\s]+)',
            cleaned, re.IGNORECASE
        )
        if not stock_match:
            # Reverse order in Indic grammar: "10 पैकेट दूध जोड़ो" / "10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸೇರಿಸಿ"
            stock_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(packets?|kg|g|l|litres?|pcs|पैक|पैकट|ಪ್ಯಾಕೆಟ್|പാക്കറ്റ്)?\s*([A-Za-z\u0900-\u0D7F\s]+?)\s*(?:add|restock|जोड़ो|सೇರಿಸಿ|ಚೇರ್ക്കുക|add karo)',
                cleaned, re.IGNORECASE
            )

        if stock_match and not any(w in lower for w in ["expense", "खर्च", "ಖರ್ಚು"]):
            qty = Decimal(stock_match.group(1))
            unit = stock_match.group(2) or "pcs"
            prod_name = stock_match.group(3).strip()
            # Clean trailing prepositions
            prod_name = re.sub(r'\b(to|in|of|karo|madi)\b', '', prod_name, flags=re.IGNORECASE).strip()
            return ParsedIntent(
                intent=IntentType.UPDATE_STOCK,
                product_name=prod_name,
                quantity=qty,
                unit=unit,
                language=effective_lang,
                requires_confirmation=True
            )

        # 12. CREATE_SALE
        # e.g. "Sell 2 kg rice for 120", "Sell 2 milk packets", "Sold 3 eggs for 18"
        sale_match = re.search(
            r'(?:sell|sold|बेंचो|बिका|ಮಾರಿ|ಮಾರಾಟ ಮಾಡಿ|വിൽക്കുക)\s*(\d+(?:\.\d+)?)\s*(packets?|kg|g|l|pcs)?\s*(?:of\s+)?([A-Za-z\u0900-\u0D7F\s]+?)(?:\s+(?:for|at|रुपये में|ರೂಪಾಯಿಗೆ|രൂപയ്ക്ക്)\s*(?:₹|rs\.?|rupees)?\s*(\d+(?:\.\d+)?))?$',
            cleaned, re.IGNORECASE
        )
        if not sale_match:
            # Indic order: "2 ಕೆಜಿ ಅಕ್ಕಿ 120 ರೂಪಾಯಿಗೆ ಮಾರಿ"
            sale_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(packets?|kg|g|l|pcs)?\s*([A-Za-z\u0900-\u0D7F\s]+?)(?:\s*(?:₹|rs\.?|rupees|रुपये|ರೂಪಾಯಿ|രൂപ)?\s*(\d+(?:\.\d+)?))?\s*(?:sell|sold|बेंचो|ಮಾರಿ|വിൽക്കുക|sale madi|sell karo)',
                cleaned, re.IGNORECASE
            )

        if sale_match:
            qty = Decimal(sale_match.group(1))
            unit = sale_match.group(2) or "pcs"
            prod_name = sale_match.group(3).strip()
            price_val = Decimal(sale_match.group(4)) if sale_match.group(4) else None
            return ParsedIntent(
                intent=IntentType.CREATE_SALE,
                product_name=prod_name,
                quantity=qty,
                unit=unit,
                price=price_val,
                language=effective_lang,
                requires_confirmation=True
            )

        # 13. ADD_EXPENSE
        # e.g. "Add expense 500 for electricity", "500 electricity expense", "500 रुपये बिजली का खर्च जोड़ो"
        if any(w in lower for w in ["expense", "खर्च", "ಖರ್ಚು", "ചെലവ്"]) and any(w in lower for w in ["add", "for", "जोड़ो", "ಸೇರಿಸಿ", "ചേർക്കുക", "payment"]):
            amt = IntentService._extract_number(cleaned)
            cat = "Miscellaneous"
            if any(w in lower for w in ["electricity", "power", "बिजली", "ವಿದ್ಯುತ್", "വൈദ്യുതി"]):
                cat = "Electricity"
            elif any(w in lower for w in ["rent", "किराया", "ಬಾಡಿಗೆ", "വാടക"]):
                cat = "Rent"
            elif any(w in lower for w in ["transport", "travel", "किराया", "ಸಾರಿಗೆ", "ഗതാഗതം"]):
                cat = "Transport"
            elif any(w in lower for w in ["salary", "wage", "वेतन", "ಸಂಬಳ", "ശമ്പളം"]):
                cat = "Salaries"

            return ParsedIntent(
                intent=IntentType.ADD_EXPENSE,
                amount=amt,
                expense_category=cat,
                description=f"Expense of ₹{amt} for {cat}" if amt else None,
                language=effective_lang,
                requires_confirmation=True
            )

        # 14. ADD_CUSTOMER
        if any(w in lower for w in ["add customer", "new customer", "ग्राहक जोड़ो", "ಹೊಸ ಗ್ರಾಹಕ", "പുതിയ ഉപഭോക്താവ്"]):
            name_part = re.sub(r'^(?:add customer|new customer|ग्राहक जोड़ो|ಹೊಸ ಗ್ರಾಹಕ|പുതിയ ഉപഭോക്താവ്)\s*', '', cleaned, flags=re.IGNORECASE).strip()
            phone_match = re.search(r'(\d{10})', name_part)
            phone = phone_match.group(1) if phone_match else None
            if phone:
                name_part = name_part.replace(phone, '').replace('phone', '').strip()

            return ParsedIntent(
                intent=IntentType.ADD_CUSTOMER,
                customer_name=name_part or "New Customer",
                customer_phone=phone,
                language=effective_lang,
                requires_confirmation=True
            )

        # UNKNOWN_INTENT
        return ParsedIntent(
            intent=IntentType.UNKNOWN_INTENT,
            confidence=0.3,
            language=effective_lang,
            requires_confirmation=False,
            is_ambiguous=True,
            clarification_question="I could not understand that command. You can say 'How much did I sell today?', 'Add 10 milk packets', or 'Sell 2 kg rice'."
        )

