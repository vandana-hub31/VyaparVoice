# Great Indian AI Internship Challenge 2026 — Competition Submission

### Applicant & Project Information
- **Project Title**: VyaparVoice — Your Shop, Ready to Speak
- **Focus Area**: Multilingual, Voice-First Business OS for Small Indian Merchants
- **Sponsor**: Gnani.ai
- **Repository Location**: `D:\VyaparVoice`

---

## 1. Challenge Criteria Alignment

### Criterion 1: Real-World Impact
Over 15 million kirana stores in India operate on paper ledgers (*bahi-khata*) or complex POS systems designed for corporate retail. VyaparVoice empowers non-technical shopkeepers to manage sales, update inventory, and reconcile customer credit simply by speaking their regional language while serving customers at the counter.

### Criterion 2: Regional & Code-Mixed Language Support
VyaparVoice natively processes:
- **Kannada** (e.g. *"ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?"*, *"10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸೇರಿಸಿ"*)
- **Malayalam** (e.g. *"ഇന്ന് എത്ര രൂപയുടെ വിൽപ്പനയായി?"*, *"രമേഷ് 200 രൂപ തന്നു"*)
- **Hindi** (e.g. *"आज कितनी बिक्री हुई?"*, *"आज कितना मुनाफा हुआ?"*)
- **Indian English & Code-Mixed Speech** (e.g. *"10 packet milk add karo"*, *"Sell 2 kg rice for 120"*)

### Criterion 3: Verified Business Actions (No Hallucinations)
VyaparVoice rejects the pattern of LLMs generating raw SQL or hallucinating mock metrics. Every query is backed by explicit SQLAlchemy aggregation functions running against PostgreSQL 18. Every state change (sales, inventory, payments) uses strict Pydantic schemas, database transactions, and two-phase expiring cryptographic tokens.

### Criterion 4: Gnani.ai AI Integration
- **Gnani Prisma STT (v3.0)**: Calls `https://api.vachana.ai/stt/v3` with telephony and regional speech optimization.
- **Gnani Timbre TTS (v3.0)**: Calls `https://api.vachana.ai/api/v1/tts/inference` to deliver expressive regional voice synthesis for business briefs and action acknowledgments.

---

## 2. Deliverables Checklist
- [x] Full source code for FastAPI backend, Next.js frontend, and PostgreSQL database.
- [x] Alembic migration versions and initial schema.
- [x] 100% passing automated test suite (`pytest tests/`).
- [x] Live competition demo account (`demo@vyaparvoice.in` / `demo12345`) with 25 Indian grocery products, 10 customers, sales records, and ledger history.
- [x] Complete documentation:
  - `README.md`
  - `docs/PROJECT_STATUS.md`
  - `docs/ARCHITECTURE.md`
  - `docs/API_DOCUMENTATION.md`
  - `docs/DATABASE_SCHEMA.md`
  - `docs/DEMO_GUIDE.md`
  - `docs/COMPETITION_SUBMISSION.md`
