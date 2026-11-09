# VyaparVoice — System Architecture

## 1. Architectural Overview

VyaparVoice is structured around a three-tier decoupled architecture:
1. **Frontend Presentation Layer**: Mobile-first Next.js 14 App Router with Tailwind CSS, Lucide Icons, and Recharts.
2. **Backend Application Layer**: Asynchronous FastAPI service running on Python 3.12, orchestrating business logic, JWT security, and NLU intent validation.
3. **Data & AI Layer**: PostgreSQL 18.6 relational database and Gnani.ai AI Services (`Prisma` for STT and `Timbre` for TTS).

```mermaid
flowchart TD
    subgraph Client ["Client Browser / Mobile PWA"]
        UI["Next.js UI & Responsive Dashboard"]
        Mic["HTML5 MediaRecorder (WAV Audio)"]
        Audio["HTML5 Audio Player"]
    end

    subgraph Backend ["FastAPI Backend (Python 3.12)"]
        Router["FastAPI Routers (/api/*)"]
        Auth["JWT Auth & Business Scoping"]
        Orchestrator["Voice Orchestrator & Safety Gate"]
        Intent["Multilingual NLU Parser"]
        Services["Business Services (Sales, Stock, Khata)"]
    end

    subgraph AI ["Gnani AI Services"]
        Prisma["Gnani Prisma v3.0 STT\n(POST api.vachana.ai/stt/v3)"]
        Timbre["Gnani Timbre v3.0 TTS\n(POST api.vachana.ai/api/v1/tts/inference)"]
    end

    subgraph Storage ["PostgreSQL 18.6"]
        DB[(11 Relational Tables\nACID Transactions)]
    end

    Mic -->|Multipart Audio| Router
    Router --> Orchestrator
    Orchestrator -->|Raw Audio| Prisma
    Prisma -->|Regional Transcription| Orchestrator
    Orchestrator --> Intent
    Intent -->|Structured Intent & Entities| Orchestrator
    Orchestrator -->|Execute / Confirm| Services
    Services -->|Strict Isolated Queries| DB
    Services -->|Actual Calculated Aggregates| Orchestrator
    Orchestrator -->|Text Response| Timbre
    Timbre -->|Base64 Voice Audio| Router
    Router --> UI
    Router --> Audio
```

---

## 2. Voice Pipeline & Two-Phase Confirmation Flow

VyaparVoice adheres to the core philosophy: **"AI that doesn't just talk — it performs real, verified business actions."**

```mermaid
sequenceDiagram
    autonumber
    actor Shopkeeper
    participant Browser as Next.js Client
    participant FastAPI as Backend API
    participant Prisma as Gnani Prisma (STT)
    participant Engine as Voice Orchestrator
    participant Postgres as PostgreSQL 18
    participant Timbre as Gnani Timbre (TTS)

    Shopkeeper->>Browser: Taps Mic & says "10 packet milk add karo"
    Browser->>FastAPI: POST /api/voice/transcribe (Audio Blob)
    FastAPI->>Prisma: Transcribe (indic-auto, prisma-v3.0)
    Prisma-->>FastAPI: "10 packet milk add karo" (kn/hi/code-mixed)
    FastAPI->>Engine: Parse Intent & Extract Entities
    Engine-->>FastAPI: Intent: UPDATE_STOCK (qty=10, prod="milk", needs_confirm=true)
    FastAPI->>Engine: Create Action Token (Expires in 5 mins)
    FastAPI->>Timbre: Synthesize confirmation prompt in shopkeeper's language
    Timbre-->>FastAPI: Spoken audio
    FastAPI-->>Browser: Prompt: "Add 10 milk packets to stock. Confirm?" + Token + Audio
    Browser->>Shopkeeper: Plays voice & displays Confirmation Card
    Shopkeeper->>Browser: Taps "Confirm & Execute"
    Browser->>FastAPI: POST /api/voice/confirm (token, confirmed=true)
    FastAPI->>Postgres: BEGIN TRANSACTION
    FastAPI->>Postgres: UPDATE products SET current_stock = current_stock + 10
    FastAPI->>Postgres: INSERT INTO inventory_transactions (RESTOCK, +10)
    FastAPI->>Postgres: COMMIT TRANSACTION
    FastAPI->>Timbre: Synthesize "Successfully updated. Milk stock is now 25 packets."
    Timbre-->>FastAPI: Voice response audio
    FastAPI-->>Browser: Success status + Updated DB figures + Audio
    Browser->>Shopkeeper: Plays verified spoken response
```

---

## 3. Database Integrity & Financial Separation

1. **Gross Profit vs Revenue**:
   - Gross Profit is strictly calculated using:
     $$\text{Gross Profit} = \sum (\text{Selling Price} - \text{Purchase Price Snapshot}) \times \text{Quantity}$$
   - The `purchase_price_snapshot` is frozen in `sale_items` at the moment of sale to prevent retroactive price shifts from distorting historical accounting.
2. **Customer Credit (Udhaar Ledger)**:
   - When a sale is made with `payment_method = 'Credit'`, an atomic debit is added to the customer's balance and logged in `credit_transactions`.
   - Repayments are recorded as positive credits, decrementing outstanding balance with full timestamping and payment tender logging.
3. **Inventory Isolation**:
   - Every product deduction is guarded against negative quantities unless explicitly configured.
   - Cancelled invoices trigger an automated rollback (`SALE_CANCEL_RESTORE`), returning quantities to stock and reversing any associated customer debt.
