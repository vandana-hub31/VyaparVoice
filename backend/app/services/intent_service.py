import re
from decimal import Decimal
from typing import Optional, Tuple
from app.schemas.intent import IntentType, ParsedIntent, IntentItem

class IntentService:
    NUM_MAP = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
        '೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4', '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9',
        '൦': '0', '൧': '1', '൨': '2', '൩': '3', '൪': '4', '൫': '5', '൬': '6', '൭': '7', '൮': '8', '൯': '9',
        '௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4', '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9',
    }

    WORD_NUM_MAP = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'एक': '1', 'दो': '2', 'तीन': '3', 'चार': '4', 'पांच': '5', 'पाँच': '5',
        'छह': '6', 'सात': '7', 'आठ': '8', 'नौ': '9', 'दस': '10',
        'ಒಂದು': '1', 'ಎರಡು': '2', 'ಮೂರು': '3', 'ನಾಲ್ಕು': '4', 'ಐದು': '5',
        'ಆರು': '6', 'ಏಳು': '7', 'ಎಂಟು': '8', 'ಒಂಬತ್ತು': '9', 'ಹತ್ತು': '10',
        'ഒന്ന്': '1', 'രണ്ട്': '2', 'മൂന്ന്': '3', 'നാല്': '4', 'അഞ്ച്': '5',
        'ആറ്': '6', 'ഏഴ്': '7', 'എട്ട്': '8', 'ഒമ്പത്': '9', 'പത്ത്': '10',
    }

    UNITS_REGEX = (
        r"packets?|pkts?|pkt|"
        r"kilograms?|kgs?|kg|"
        r"grams?|gms?|g|"
        r"litres?|liters?|ltrs?|ltr|l|"
        r"pieces?|pcs?|"
        r"boxes?|box|"
        r"bottles?|bott|"
        r"cans?|"
        # Hindi
        r"पैकेट|पैकट|पैक|किलोग्राम|किलो|ग्राम|लीटर|पीस|डिब्बा|बोतल|"
        # Kannada
        r"ಪ್ಯಾಕೆಟ್|ಕಿಲೋಗ್ರಾಂ|ಕಿಲೋ|ಕೆಜಿ|ಗ್ರಾಂ|ಲೀಟರ್|ಪೀಸ್|ಡಬ್ಬಿ|ಬಾಟಲಿ|"
        # Malayalam
        r"പാക്കറ്റ്|കിലോഗ്രാം|കിലോ|ഗ്രാം|ലിറ്റർ|പീസ്|കുപ്പി|"
        # Tamil
        r"பாக்கெட்|கிலோகிராம்|கிலோ|கிராம்|லிட்டர்|பீஸ்|பாட்டில்"
    )

    SALE_VERBS_PREFIX = (
        r"(?:(?:today\s+)?(?:i|we|just)\s+)?(?:have\s+)?(?:sold|sell|sale|recorded\s+sale|bill|billed)|"
        r"बेचो|बेंचो|बेच|बिका|बिक्री|बेचना|बेची|बेचा|"
        r"ಮಾರಿರಿ|ಮಾರಿ|ಮಾರಾಟ\s+ಮಾಡಿ|ಮಾರಾಟ\s+ಮಾಡಿದೆ|ಮಾರಾಟ\s+ಮಾಡಿದ|ಮಾರಾಟ|ಮಾರಿದೆ|ಮಾರಿದ್ದೇನೆ|"
        r"വിൽക്കുക|വിറ്റു|വിൽക്കുകയാണ്|വിൽപ്പന|വിൽക്ക്|"
        r"விற்கவும்|விற்க|விற்று|விற்பனை"
    )

    SALE_VERBS_POSTFIX = (
        r"sell|sold|sale|sell\s+karo|sale\s+madi|sale\s+panunga|"
        r"बेचो|बेंचो|बेच|बिका|बिक्री|बेचना|बेची|बेचा|बेच\s+दिया|बेच\s+दो|सेल\s+करो|"
        r"ಮಾರಿರಿ|ಮಾರಿ|ಮಾರಾಟ\s+ಮಾಡಿ|ಮಾರಾಟ\s+ಮಾಡಿದೆ|ಮಾರಾಟ\s+ಮಾಡಿದ|ಮಾರಾಟ|ಮಾರಿದೆ|ಮಾರಿಬಿಡಿ|ಮಾರಿದ್ದೇನೆ|ಸೇಲ್\s+ಮಾಡಿ|"
        r"വിൽക്കുക|വിറ്റു|വിൽക്കുകയാണ്|വിൽപ്പന|വിൽക്ക്|വിൽക്കണം|സെയിൽ\s+ചെയ്യുക|"
        r"விற்கவும்|விற்க|விற்று|விற்பனை"
    )

    PRICE_PATTERN = (
        r"(?:"
        r"(?:for|at)\s*(?:₹|rs\.?|rupees)?\s*(\d+(?:\.\d+)?)(?:\s*(?:rs\.?|rupees?))?|"
        r"(?:₹|rs\.?)\s*(\d+(?:\.\d+)?)|"
        r"(\d+(?:\.\d+)?)\s*(?:रुपये\s*में|रुपए\s*में|रुपये|रुपए|रु|ರೂಪಾಯಿಗೆ|ರೂಗೆ|ರೂಪಾಯಿ|ರೂ|ಕ್ಕೆ|ಗೆ|രൂപയ്ക്ക്|രൂപക്ക്|രൂപ|ന്|ക്ക്|ரூபாய்க்கு|ரூபாய்|ரூ|rs\.?|rupees?)"
        r")"
    )

    STOCK_VERBS_PREFIX = (
        r"(?:(?:today\s+)?(?:i|we|just)\s+)?(?:have\s+)?(?:add|added|restock|restocked|stock|stock\s+up)|"
        r"जोड़ो|डालो|रखो|शामिल\s+करो|"
        r"ಸೇರಿಸಿ|ಸೇರಿಸು|ಹಾಕಿ|ಹಾಕು|"
        r"ചേർക്കുക|ചേർക്കൂ|ഇടുക|"
        r"சேர்க்கவும்|சேர்"
    )

    STOCK_VERBS_POSTFIX = (
        r"add|restock|stock|add\s+karo|add\s+madi|add\s+panunga|"
        r"(?:स्टॉक\s+में\s+)?(?:जोड़ो|डालो|रखो)|स्टॉक\s+जोड़ो|ऐड\s+करो|"
        r"(?:ಸ್ಟಾಕ್(?:ಗೆ|್‌ಗೆ|\s+ಗೆ|\s+ನಲ್ಲಿ)?\s*)?(?:ಸೇರಿಸಿ|ಸೇರಿಸು|ಹಾಕಿ|ಹಾಕು)|ಸ್ಟಾಕ್\s+ಸೇರಿಸಿ|ಆಡ್\s+ಮಾಡಿ|ಆಡ್\s+ಮಾಡು|"
        r"(?:സ്റ്റോക്കിൽ|സ്റ്റോക്കിലേക്ക്|സ്റ്റോക്ക്)?\s*(?:ചേർക്കുക|ചേർക്കൂ|ഇടുക)|ആഡ്\s+ചെയ്യുക|"
        r"சேர்க்கவும்|சேர்|ஸ்டாக்\s+சேர்க்கவும்"
    )

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalizes sentence-ending punctuation, Indic digits, and common number words.
        """
        cleaned = text.strip()
        cleaned = re.sub(r'[\.।॥\?!,;:।॥]+$', '', cleaned).strip()
        cleaned = re.sub(r'^[\.।॥\?!,;:।॥]+', '', cleaned).strip()

        for k, v in IntentService.NUM_MAP.items():
            cleaned = cleaned.replace(k, v)

        for word, num in IntentService.WORD_NUM_MAP.items():
            cleaned = re.sub(rf'(^|\s){re.escape(word)}(\s+)', rf'\g<1>{num}\g<2>', cleaned, flags=re.IGNORECASE)

        return cleaned

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect language from Unicode block ranges and Romanized/code-mixed keywords.
        Supports:
        - Kannada: kn
        - Malayalam: ml
        - Hindi: hi
        - Tamil: ta
        - English: en
        """
        for char in text:
            if '\u0C80' <= char <= '\u0CFF':
                return "kn"
            if '\u0D00' <= char <= '\u0D7F':
                return "ml"
            if '\u0900' <= char <= '\u097F':
                return "hi"
            if '\u0B80' <= char <= '\u0BFF':
                return "ta"

        lower = text.lower()
        if re.search(r'\b(becho|bika|bikri|jodo|daalo|karo|doodh|chawal|aata|cheeni|shakkar|tel|paani|rupaye|rupya|udhar|kharch|kharcha|bhai|kitna|aaj)\b', lower):
            return "hi"
        if re.search(r'\b(mariri|mari|haaki|serisi|madi|akki|haalu|bele|yenne|saala|kharchu|roopayi|eshtu|ivattu|ivattina|baki)\b', lower):
            return "kn"
        if re.search(r'\b(vilkkuka|vittu|cherkkuka|cherkku|paal|ari|roopa|chilavu|innathe|ethra|kadam|kudissika)\b', lower):
            return "ml"
        if re.search(r'\b(vikkavum|vitru|serkkavum|ser|panunga|paal|arisi|selavu|inraiya|evvalavu|kadan)\b', lower):
            return "ta"

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
        cleaned = IntentService.normalize_text(text)
        lower = cleaned.lower()
        detected_lang = IntentService.detect_language(cleaned)

        if detected_lang in ["kn", "ml", "hi", "ta"]:
            effective_lang = detected_lang
        elif user_lang and user_lang not in ["auto", "indic-auto"]:
            has_english_words = bool(re.search(r'\b(sell|sold|add|stock|restock|today\'?s?|sales|profit|expense|rice|milk|eggs?|customer|owes|paid)\b', lower))
            if has_english_words and user_lang != "en":
                effective_lang = "en"
            else:
                effective_lang = user_lang
        else:
            effective_lang = detected_lang

        # 1. GET_DAILY_SUMMARY
        clean_text_for_summary = re.sub(r'[\?\.!,;]', '', lower).strip()
        daily_summary_patterns = [
            # Kannada
            r'ವ್ಯಾಪಾರದ\s+ಬಗ್ಗೆ',
            r'ವ್ಯಾಪಾರ\s+ಹೇಗಿದೆ',
            r'ವ್ಯವಹಾರ\s+ಹೇಗಿದೆ',
            r'ಎಷ್ಟು\s+ವ್ಯಾಪಾರ\s+ಆಗಿದೆ',
            r'ಇಂದಿನ\s+ಮಾರಾಟ\s+ಎಷ್ಟು',
            r'ಇವತ್ತಿನ\s+ಮಾರಾಟ\s+ಎಷ್ಟು',
            r'ಇವತ್ತಿನ\s+ಲೆಕ್ಕ',
            r'ಆದಾಯ\s+ಮತ್ತು\s+ಖರ್ಚು',
            r'ವ್ಯವಹಾರ\s+ಸಾರಾಂಶ',
            r'ದೈನಂದಿನ\s+ಸಾರಾಂಶ',
            # English
            r'today\'?s?\s+business',
            r'business\s+today',
            r'daily\s+(?:business\s+)?summary',
            r'today\'?s?\s+summary',
            r'give\s+me\s+today\'?s?\s+summary',
            r'today\'?s?\s+revenue\s+and\s+expenses',
            # Hindi
            r'व्यापार\s+कैसा',
            r'कारोबार\s+कैसा',
            r'व्यापार\s+के\s+बारे',
            r'कारोबार\s+के\s+बारे',
            r'आज\s+का\s+हिसाब',
            r'आय\s+और\s+खर्च',
            r'दैनिक\s+सारांश',
            r'व्यापार\s+सारांश',
            # Malayalam
            r'ബിസിനസ്സ്\s+എങ്ങനെയുണ്ട്',
            r'കച്ചവടം\s+എങ്ങനെയുണ്ട്',
            r'ബിസിനസ്സ്\s+വിവരം',
            r'ഇന്നത്തെ\s+കണക്ക്',
            r'വരുമാനവും\s+ചെലവും',
            r'ദിവസേനയുള്ള\s+വിവരണം',
            # Tamil
            r'வியாபாரம்\s+எப்படி',
            r'வியாபாரத்தை\s+பற்றி',
            r'இன்றைய\s+கணக்கு',
            r'வருமானம்\s+மற்றும்\s+செலவு',
            r'வியாபார\s+சுருக்கம்'
        ]
        if any(re.search(p, lower) or re.search(p, clean_text_for_summary) for p in daily_summary_patterns):
            return ParsedIntent(
                intent=IntentType.GET_DAILY_SUMMARY,
                language=effective_lang,
                requires_confirmation=False,
                time_period="today"
            )

        # 2. GET_TODAYS_SALES
        todays_sales_patterns = [
            r"(?:today\'?s?|daily).*(?:sales?|sold|revenue)|how\s+much.*(?:did\s+i\s+)?sell",
            r"(?:ಇವತ್ತು|ಇವತ್ತಿನ|ಇಂದಿನ).*(?:ಮಾರಾಟ|ವ್ಯಾಪಾರ|ಸೇಲ್)|(?:ಮಾರಾಟ|ವ್ಯಾಪಾರ|ಸೇಲ್).*(?:ಎಷ್ಟು|ಆಯಿತು|ಆಗಿದೆ)",
            r"(?:आज|दैनिक).*(?:बिक्री|बिका|सेल्स|सेल)|(?:बिक्री|बिका|कारोबार).*(?:कितनी|कितना)",
            r"(?:ഇന്ന്|ഇന്നത്തെ|ദിവസേന).*(?:വിൽപ്പന|കച്ചവടം|സെയിൽസ്|സെയിൽ)|(?:വിൽപ്പന|കച്ചവടം).*(?:എത്ര|നടന്നു)",
            r"(?:இன்று|இன்றைய).*(?:விற்பனை|விற்றோம்)"
        ]
        if any(re.search(p, lower) for p in todays_sales_patterns):
            return ParsedIntent(
                intent=IntentType.GET_TODAYS_SALES,
                language=effective_lang,
                requires_confirmation=False,
                time_period="today"
            )

        # 3. GET_PROFIT_SUMMARY
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

        # 4. GET_EXPENSE_SUMMARY
        expense_query_patterns = [
            r"(?:show|what|total|today\'?s?|my).*(?:expense|spending|cost)",
            r"(?:ಇವತ್ತಿನ|ಇಂದಿನ|ಒಟ್ಟು|ನನ್ನ|ಎಷ್ಟು).*(?:ಖರ್ಚು|ವೆಚ್ಚ)",
            r"(?:आज|कुल|मेरा|कितना).*(?:खर्च|खर्चे)",
            r"(?:ഇന്നത്തെ|ആകെ|എന്റെ|എത്ര).*(?:ചെലവ്|ചെലവുകൾ)",
            r"(?:இன்றைய|மொத்த).*(?:செலவு)"
        ]
        if any(re.search(p, lower) for p in expense_query_patterns) and not any(w in lower for w in ["add", "जोड़ो", "ಸೇರಿಸಿ", "ಹಾಕಿ", "ചേർക്കുക", "സേർ"]) and not re.search(r'\d+', lower):
            return ParsedIntent(
                intent=IntentType.GET_EXPENSE_SUMMARY,
                language=effective_lang,
                requires_confirmation=False,
                time_period="today"
            )

        # 5. GET_LOW_STOCK
        if any(w in lower for w in [
            "low stock", "low-stock", "running low", "shortage", "out of stock", "which items are low", "what products are running low",
            "कम स्टॉक", "खत्म होने वाला", "कौन से उत्पाद कम",
            "ಕಡಿಮೆ ಸ್ಟಾಕ್", "ಸ್ಟಾಕ್ ಕಡಿಮೆ", "ಖಾಲಿಯಾಗುತ್ತಿರುವ",
            "കുറഞ്ഞ സ്റ്റോക്ക്", "സ്റ്റോക്ക് കുറവ്", "തീരാറായ",
            "குறைந்த சரக்கு", "சரக்கு குறைவு"
        ]):
            return ParsedIntent(
                intent=IntentType.GET_LOW_STOCK,
                language=effective_lang,
                requires_confirmation=False
            )

        # 6. GET_TOP_PRODUCTS
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

        # 7. GET_SALES_SUMMARY
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

        # 8. GET_INVENTORY
        if any(w in lower for w in [
            "show inventory", "inventory list", "all stock", "product stock", "stock of",
            "स्टॉक सूची", "इन्वेंट्री",
            "ಇನ್ವೆಂಟರಿ", "ದಾಸ್ತಾನು",
            "ಇൻവെന്ററി", "സ്റ്റോക്ക് വിവരം",
            "சரக்கு பட்டியல்", "இருப்பு விவரம்"
        ]) and not any(w in lower for w in ["add", "जोड़ो", "ಸೇರಿಸಿ", "ಹಾಕಿ", "ചേർക്കുക"]):
            return ParsedIntent(
                intent=IntentType.GET_INVENTORY,
                language=effective_lang,
                requires_confirmation=False
            )

        # 9. RECORD_REPAYMENT
        repay_pattern = re.search(r'([A-Za-z\u0900-\u0D7F]+)\s+(?:paid|gives|gave|returned|ने|ಕೊಟ್ಟರು|തന്നു|കൊடுத்தார்)\s*(?:₹|rs\.?|rupees|रुपये|ರೂಪಾಯಿ|രൂപ)?\s*(\d+(?:\.\d+)?)', cleaned, re.IGNORECASE)
        if repay_pattern or "repayment" in lower:
            cust_name = repay_pattern.group(1).strip() if repay_pattern else None
            amount = Decimal(repay_pattern.group(2)) if repay_pattern else None
            if cust_name and cust_name.lower() in ["customer", "from", "ने"]:
                cust_name = None

            return ParsedIntent(
                intent=IntentType.RECORD_REPAYMENT,
                customer_name=cust_name,
                amount=amount,
                language=effective_lang,
                requires_confirmation=True
            )

        # 10. CREATE_CREDIT
        credit_pattern = re.search(r'([A-Za-z\u0900-\u0D7F]+)\s+(?:owes|borrowed|उधार|ಸಾಲ|കടം)\s*(?:me)?\s*(?:₹|rs\.?|rupees|रुपये|ರೂಪಾಯಿ|രൂപ)?\s*(\d+(?:\.\d+)?)', cleaned, re.IGNORECASE)
        if credit_pattern or ("credit" in lower and any(w in lower for w in ["owes", "give", "to", "उधार", "ಸಾಲ"])):
            cust_name = credit_pattern.group(1).strip() if credit_pattern else None
            amount = Decimal(credit_pattern.group(2)) if credit_pattern else None
            return ParsedIntent(
                intent=IntentType.CREATE_CREDIT,
                customer_name=cust_name,
                amount=amount,
                language=effective_lang,
                requires_confirmation=True
            )

        # 11. GET_CUSTOMER_BALANCE
        if any(w in lower for w in ["owe", "owes", "balance", "बकाया", "ಉಳಿಕೆ", "ಬಾಕಿ", "കുടിശ്ശിക", "கடன்"]) and not any(w in lower for w in ["paid", "repay", "credit", "उधार", "ಸಾಲ"]):
            name_match = re.search(r'([A-Za-z\u0900-\u0D7F]+?)(?:\'s)?\s+(?:balance|owe|owes|का\s+बकाया|बकाया|ಅವರ\s+ಬಾಕಿ|ಬಾಕಿ|ന്റെ\s+കുടിശ്ശിക|കുടിശ്ശിക|கடன்)', cleaned, re.IGNORECASE)
            c_name = name_match.group(1).strip() if name_match else None
            if not c_name and re.search(r'how\s+much\s+does\s+([A-Za-z\u0900-\u0D7F]+)\s+owe', cleaned, re.IGNORECASE):
                c_name = re.search(r'how\s+much\s+does\s+([A-Za-z\u0900-\u0D7F]+)\s+owe', cleaned, re.IGNORECASE).group(1).strip()
            if not c_name:
                first_w = cleaned.split()[0]
                if first_w.lower() not in ["how", "what", "show", "check", "give", "tell", "ಇವತ್ತು", "आज", "ഇന്ന്"]:
                    c_name = first_w
            if c_name:
                c_name = re.sub(r'(\'s|ന്റെ|ರ|ಅವರ)$', '', c_name).strip()

            return ParsedIntent(
                intent=IntentType.GET_CUSTOMER_BALANCE,
                customer_name=c_name,
                language=effective_lang,
                requires_confirmation=False
            )

        # 12. CREATE_SALE
        if not any(w in lower for w in ["expense", "खर्च", "ಖರ್ಚು", "ചെലവ്", "செலவு"]):
            # Pattern 1: Verb at beginning: e.g. "Sell 2 kg rice for 120", "I sold 2 kg rice for 120 rupees"
            p_sale1 = rf'^(?:{IntentService.SALE_VERBS_PREFIX})\s+(\d+(?:\.\d+)?)\s*(?:({IntentService.UNITS_REGEX})\s+)?(?:of\s+)?(.+?)(?:\s+{IntentService.PRICE_PATTERN})?$'
            m_sale1 = re.search(p_sale1, cleaned, re.IGNORECASE)
            if m_sale1:
                qty = Decimal(m_sale1.group(1))
                unit = m_sale1.group(2) or "pcs"
                prod = m_sale1.group(3).strip()
                price_str = m_sale1.group(4) or m_sale1.group(5) or m_sale1.group(6)
                price = Decimal(price_str) if price_str else None
                prod = re.sub(r'^(?:of)\s+', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'\b(?:to|in|of|karo|madi|panunga)\b', '', prod, flags=re.IGNORECASE).strip()
                if prod:
                    return ParsedIntent(
                        intent=IntentType.CREATE_SALE,
                        product_name=prod,
                        quantity=qty,
                        unit=unit,
                        price=price,
                        language=effective_lang,
                        requires_confirmation=True
                    )

            # Pattern 2: Postfix verb (Indic / SOV order): e.g. "2 पैकेट दूध बेचो", "2 ಕೆಜಿ ಅಕ್ಕಿ 120 ರೂಪಾಯಿಗೆ ಮಾರಾಟ ಮಾಡಿದೆ"
            p_sale2 = rf'^\s*(\d+(?:\.\d+)?)\s*(?:({IntentService.UNITS_REGEX})\s+)?(?:of\s+)?(.+?)(?:\s+{IntentService.PRICE_PATTERN})?\s+(?:{IntentService.SALE_VERBS_POSTFIX})\s*$'
            m_sale2 = re.search(p_sale2, cleaned, re.IGNORECASE)
            if m_sale2:
                qty = Decimal(m_sale2.group(1))
                unit = m_sale2.group(2) or "pcs"
                prod = m_sale2.group(3).strip()
                price_str = m_sale2.group(4) or m_sale2.group(5) or m_sale2.group(6)
                price = Decimal(price_str) if price_str else None
                prod = re.sub(r'^(?:of)\s+', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'\b(?:to|in|of|karo|madi|panunga)\b', '', prod, flags=re.IGNORECASE).strip()
                if prod:
                    return ParsedIntent(
                        intent=IntentType.CREATE_SALE,
                        product_name=prod,
                        quantity=qty,
                        unit=unit,
                        price=price,
                        language=effective_lang,
                        requires_confirmation=True
                    )

            # Pattern 3: Inverted order: e.g. "Sell milk 2 packets for 50"
            p_sale3 = rf'^(?:{IntentService.SALE_VERBS_PREFIX})\s+(.+?)\s+(\d+(?:\.\d+)?)\s*({IntentService.UNITS_REGEX})?(?:\s+{IntentService.PRICE_PATTERN})?$'
            m_sale3 = re.search(p_sale3, cleaned, re.IGNORECASE)
            if m_sale3:
                prod = m_sale3.group(1).strip()
                qty = Decimal(m_sale3.group(2))
                unit = m_sale3.group(3) or "pcs"
                price_str = m_sale3.group(4) or m_sale3.group(5) or m_sale3.group(6)
                price = Decimal(price_str) if price_str else None
                prod = re.sub(r'^(?:of)\s+', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'\b(?:to|in|of|karo|madi|panunga)\b', '', prod, flags=re.IGNORECASE).strip()
                if prod:
                    return ParsedIntent(
                        intent=IntentType.CREATE_SALE,
                        product_name=prod,
                        quantity=qty,
                        unit=unit,
                        price=price,
                        language=effective_lang,
                        requires_confirmation=True
                    )

        # 13. UPDATE_STOCK
        if not any(w in lower for w in ["expense", "खर्च", "ಖರ್ಚು", "ചെലവ്", "செലவு"]):
            # Prefix verb: e.g. "Add 10 packets of milk"
            p_stock1 = rf'^(?:{IntentService.STOCK_VERBS_PREFIX})\s+(\d+(?:\.\d+)?)\s*(?:({IntentService.UNITS_REGEX})\s+)?(?:of\s+)?(.+?)$'
            m_stock1 = re.search(p_stock1, cleaned, re.IGNORECASE)
            if m_stock1:
                qty = Decimal(m_stock1.group(1))
                unit = m_stock1.group(2) or "pcs"
                prod = m_stock1.group(3).strip()
                prod = re.sub(r'^(?:of)\s+', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'\b(?:to\s+stock|in\s+stock|to|in|of|karo|madi|panunga)\b', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'(?:ಸ್ಟಾಕ್(?:ಗೆ|್‌ಗೆ|\s+ಗೆ|\s+ನಲ್ಲಿ)?|स्टॉक\s*में|സ്റ്റോക്കിൽ|സ്റ്റോക്കിലേക്ക്|സ്റ്റോക്ക്|ஸ்டாக்கில்)', '', prod).strip()
                if prod:
                    return ParsedIntent(
                        intent=IntentType.UPDATE_STOCK,
                        product_name=prod,
                        quantity=qty,
                        unit=unit,
                        language=effective_lang,
                        requires_confirmation=True
                    )

            # Postfix verb: e.g. "10 पैकेट दूध स्टॉक में जोड़ो", "10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸ್ಟಾಕ್ಗೆ ಸೇರಿಸು", "10 പാക്കറ്റ് പാൽ സ്റ്റോക്കിൽ ചേർക്കുക"
            p_stock2 = rf'^\s*(\d+(?:\.\d+)?)\s*(?:({IntentService.UNITS_REGEX})\s+)?(?:of\s+)?(.+?)\s+(?:{IntentService.STOCK_VERBS_POSTFIX})\s*$'
            m_stock2 = re.search(p_stock2, cleaned, re.IGNORECASE)
            if m_stock2:
                qty = Decimal(m_stock2.group(1))
                unit = m_stock2.group(2) or "pcs"
                prod = m_stock2.group(3).strip()
                prod = re.sub(r'^(?:of)\s+', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'\b(?:to\s+stock|in\s+stock|to|in|of|karo|madi|panunga)\b', '', prod, flags=re.IGNORECASE).strip()
                prod = re.sub(r'(?:ಸ್ಟಾಕ್(?:ಗೆ|್‌ಗೆ|\s+ಗೆ|\s+ನಲ್ಲಿ)?|स्टॉक\s*में|സ്റ്റോക്കിൽ|സ്റ്റോക്കിലേക്ക്|സ്റ്റോക്ക്|ஸ்டாக்கில்)', '', prod).strip()
                if prod:
                    return ParsedIntent(
                        intent=IntentType.UPDATE_STOCK,
                        product_name=prod,
                        quantity=qty,
                        unit=unit,
                        language=effective_lang,
                        requires_confirmation=True
                    )

        # 14. ADD_EXPENSE
        if any(w in lower for w in ["expense", "खर्च", "ಖರ್ಚು", "ചെലവ്"]) and any(w in lower for w in ["add", "for", "जोड़ो", "ಸೇರಿಸಿ", "ಹಾಕಿ", "ചേർക്കുക", "payment", "ಖರ್ಚು"]) and re.search(r'\d+', lower):
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

        # 15. ADD_CUSTOMER
        if any(w in lower for w in ["add customer", "new customer", "ग्राहक जोड़ो", "ಹೊಸ ಗ್ರಾಹಕ", "ಪುതിയ ഉപഭോക്താവ്"]):
            name_part = re.sub(r'^(?:add customer|new customer|ग्राहक जोड़ो|ಹೊಸ ಗ್ರಾಹಕ|ಪುതിയ ഉപഭോക്താവ്)\s*', '', cleaned, flags=re.IGNORECASE).strip()
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
