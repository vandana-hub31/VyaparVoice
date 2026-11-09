# VyaparVoice — Competition Demonstration Guide

**Great Indian AI Internship Challenge 2026 by Gnani.ai**  
*Evaluation & Live Demonstration Walkthrough*

---

## 1. Quick Launch Setup

### Pre-requisites Verified
- PostgreSQL running on port 5433 (or standard port)
- FastAPI backend on `http://localhost:8000`
- Next.js frontend on `http://localhost:3000`

### 1-Click Access
1. Open browser at `http://localhost:3000`
2. Click **"1-Click Live Competition Demo"** or sign in with:
   - **Email:** `demo@vyaparvoice.in`
   - **Password:** `demo12345`
3. Click the top-bar **"Reset Demo Data"** anytime to reset the store to baseline.

---

## 2. Recommended 60-Second Competition Demo Script

| Step | Action | Spoken Command / Interaction | Verified System Outcome |
|---|---|---|---|
| **1** | Open Dashboard | Navigate to `/dashboard` | Executive KPIs show Today's Sales, Profit, Credit Due from real PostgreSQL records. |
| **2** | Voice Query: Today's Sales | Click Mic or use Voice Assistant: *"How much did I sell today?"* | **Backend calculates real SQL SUM** of today's non-cancelled sales invoices. Voice replies with exact figure and transaction count. |
| **3** | Multilingual Query (Kannada) | Say or select: *"ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?"* | Language auto-detected as Kannada (`kn`). Assistant replies in Kannada: *"ಇವತ್ತಿನ ಒಟ್ಟು ಮಾರಾಟ ₹... ಆಗಿದೆ."* |
| **4** | Voice Mutation with Safety Confirmation | Say: *"Add 5 packets of milk"* | Assistant parses intent `UPDATE_STOCK`, locates Nandini Milk, and generates a **Safety Confirmation Card** with 5-minute cryptographic token. |
| **5** | Confirmation & Execution | Click **"Confirm & Execute"** | Backend performs atomic DB write, increments stock by 5 in `products`, logs transaction in `inventory_transactions`, and responds: *"Successfully updated. Milk stock is now 40 pkt."* |
| **6** | Verified Inventory Audit | Click **Inventory** (`/inventory`) | Judges see updated stock of 40 pkt and new RESTOCK transaction row. |
| **7** | Audio Daily Summary | Return to Dashboard and click **"Hear Voice Summary"** | Gnani Timbre synthesizes a daily business brief in Kannada / Malayalam / Hindi directly derived from live aggregates. |

---

## 3. Advanced Multi-lingual Prompts to Test

### Kannada (ಕನ್ನಡ)
- *"ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?"* (What are today's sales?)
- *"10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸೇರಿಸಿ"* (Add 10 packets milk)
- *"ರಮೇಶ್ ಬಾಕಿ ಎಷ್ಟು?"* (How much does Ramesh owe?)

### Malayalam (മലയാളം)
- *"ഇന്ന് എത്ര രൂപയുടെ വിൽപ്പനയായി?"* (What are today's sales?)
- *"10 പാക്കറ്റ് പാൽ ചേർക്കുക"* (Add 10 packets milk)
- *"രമേഷ് 200 രൂപ തന്നു"* (Ramesh paid 200 rupees repayment)

### Hindi (हिन्दी)
- *"आज कितनी बिक्री हुई?"* (How much did I sell today?)
- *"आज कितना मुनाफा हुआ?"* (How much gross profit did I make today?)
- *"कम स्टॉक वाले उत्पाद दिखाओ"* (Show low stock items)
- *"रमेश ने 200 रुपये दिए"* (Record 200 rupees repayment from Ramesh)

### Code-Mixed (Hinglish / Kanglish)
- *"10 packet milk add karo"*
- *"Sell 2 kg rice for 120"*
