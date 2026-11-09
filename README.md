# VyaparVoice — Your Shop, Ready to Speak

**VyaparVoice** is a complete, production-grade, voice-first business management application for small Indian shopkeepers (kirana store owners, provision merchants, and local retail outlets), built for the **Great Indian AI Internship Challenge 2026 by Gnani.ai**.

VyaparVoice transforms daily store administration by allowing shopkeepers to record sales, manage inventory, audit customer credit ledgers (*udhaari khata*), and hear daily business summaries using natural voice commands in **Kannada, Malayalam, Hindi, and English**.

---

## 🌟 Key Highlights

- **AI That Performs Verified Actions**: Every business figure is calculated strictly from live PostgreSQL 18.6 records. No fabricated metrics or hallucinated numbers.
- **Gnani.ai Speech Integration**:
  - **Gnani Prisma STT (v3.0)**: Telephony-grade, noise-resistant Indian speech recognition.
  - **Gnani Timbre TTS (v3.0)**: Expressive regional language speech synthesis.
- **Multilingual Support**: Supports Kannada (ಕನ್ನಡ), Malayalam (മലയാളം), Hindi (हिन्दी), Indian English, and code-mixed speech (e.g. *"10 packet milk add karo"*).
- **Two-Phase Safety Confirmation**: Sensitive mutations (stock updates, sales, expenses, repayments) generate an expiring confirmation token before writing to PostgreSQL.
- **Double-Entry Khata Ledger**: Customer debts and repayments are recorded with full audit trails and payment tender tracking.
- **Accurate Financial Separation**: Gross profit is strictly calculated based on purchase price snapshots taken at the time of sale, distinguishing sales revenue from profit.
- **Mobile-First SaaS UI**: Responsive Next.js 14 interface featuring an executive dashboard, Recharts analytics, and floating voice control.

---

## 🛠 Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons, Recharts
- **Backend**: FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0, Alembic, PyJWT, Bcrypt
- **Database**: PostgreSQL 18.6 (ACID transactions, UUIDs, numeric currency precision)
- **AI & Speech**: Gnani Prisma STT (v3.0) & Gnani Timbre TTS (v3.0)

---

## 📂 Project Structure

```text
D:\VYAPARVOICE
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── models/           # SQLAlchemy database entities (11 models)
│   │   ├── schemas/          # Pydantic v2 validation schemas
│   │   ├── services/         # Business logic, NLU parser & Gnani AI services
│   │   ├── routers/          # FastAPI REST endpoints
│   │   ├── utils/            # JWT auth, password security, and dependencies
│   │   ├── config.py         # App configuration & settings
│   │   ├── database.py       # PostgreSQL connection & SessionLocal
│   │   └── main.py           # FastAPI application root
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Backend configuration
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages (18 routes)
│   │   ├── components/       # Navbar, Sidebar, BottomNav, Modals
│   │   ├── context/          # AuthContext & Language state
│   │   └── lib/              # API fetch client & regional translations
│   ├── package.json          # Node dependencies
│   └── tailwind.config.ts    # Tailwind styling config
├── tests/                    # Automated pytest suite
├── docs/                     # Project documentation
│   ├── PROJECT_STATUS.md
│   ├── ARCHITECTURE.md
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_SCHEMA.md
│   ├── DEMO_GUIDE.md
│   └── COMPETITION_SUBMISSION.md
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Database Configuration
Ensure PostgreSQL is running (default port 5433 or 5432). Configure `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres@localhost:5433/vyaparvoice
TEST_DATABASE_URL=postgresql+psycopg://postgres@localhost:5433/vyaparvoice_test
SECRET_KEY=vyaparvoice_super_secret_jwt_key_2026_gnani_ai_challenge
GNANI_API_KEY=<your_api_key_optional>
```

Run Alembic database migrations:
```powershell
cd D:\VYAPARVOICE\backend
python -m alembic upgrade head
```

### 2. Backend Startup
Start the FastAPI server:
```powershell
cd D:\VYAPARVOICE\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 3. Frontend Startup
Install packages and start the Next.js server:
```powershell
cd D:\VYAPARVOICE\frontend
npm install
npm run build
npm run start
```
Frontend will be available at `http://localhost:3000`.

---

## 🎯 1-Click Competition Demo

1. Open `http://localhost:3000` in your web browser.
2. Click **"1-Click Live Competition Demo"** or sign in with:
   - **Email:** `demo@vyaparvoice.in`
   - **Password:** `demo12345`
3. The store is pre-loaded with **25 authentic Indian grocery items, 10 customer khata ledgers, recent sales, and expenses**.
4. Tap **"Reset Demo Data"** at the top right anytime to restore the pristine competition state.

---

## 🧪 Automated Testing

Run the comprehensive pytest suite:
```powershell
cd D:\VYAPARVOICE
python -m pytest tests/ -v
```
All 6 test suites cover authentication, product CRUD, inventory deduction, idempotency keys, sale cancellation stock rollback, customer credit ledgers, and multilingual intent parsing.

---

## 🎙️ Gnani AI Integration Details

- **Prisma STT**: `POST https://api.vachana.ai/stt/v3`
  - Audio Format: WAV (telephony & 16kHz)
  - Models: `prisma-v3.0`
  - Language Code: `indic-auto` (or `kn-IN`, `ml-IN`, `hi-IN`, `en-IN`)
- **Timbre TTS**: `POST https://api.vachana.ai/api/v1/tts/inference`
  - Voice: `Nalini`
  - Models: `timbre-v3.0`
  - Languages: Kannada, Malayalam, Hindi, Indian English

---

## 📜 License
Developed for the **Great Indian AI Internship Challenge 2026 by Gnani.ai**.
All rights reserved.

