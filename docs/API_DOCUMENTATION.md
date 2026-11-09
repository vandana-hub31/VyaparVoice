# VyaparVoice — API Documentation

The VyaparVoice backend is built with FastAPI and runs on `http://localhost:8000`. Full interactive Swagger OpenAPI docs are available at `/docs` and ReDoc at `/redoc`.

All business endpoints require a JWT Bearer token passed in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```
Optionally, pass `X-Business-ID: <uuid>` to target a specific business profile.

---

## 1. Authentication (`/api/auth`)

### `POST /api/auth/register`
Create a new shopkeeper user account and initialize a default business.
- **Request Body**:
  ```json
  {
    "full_name": "Ramesh Gowda",
    "email": "ramesh@example.com",
    "password": "securepassword123",
    "phone": "9845012345",
    "preferred_language": "kn"
  }
  ```
- **Response**: `201 Created` with User object (password omitted).

### `POST /api/auth/login`
Authenticate shopkeeper credentials and obtain an access token.
- **Request Body**:
  ```json
  {
    "email": "demo@vyaparvoice.in",
    "password": "demo12345"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": { ... }
  }
  ```

### `GET /api/auth/me`
Retrieve currently authenticated user profile.

---

## 2. Businesses (`/api/businesses`)

- `GET /api/businesses`: List all businesses owned by the user.
- `GET /api/businesses/current`: Get active business profile.
- `POST /api/businesses`: Create a new business profile.
- `PUT /api/businesses/{business_id}`: Update business details (name, GSTIN, currency, address).

---

## 3. Executive Dashboard (`/api/dashboard`)

### `GET /api/dashboard/summary`
Calculates real-time business figures from PostgreSQL:
- `today_sales`: Total non-cancelled sales amount today.
- `today_expenses`: Total operating expenses recorded today.
- `estimated_gross_profit`: Computed from `(selling_price - purchase_price_snapshot) * quantity`.
- `transaction_count`: Number of completed sales today.
- `outstanding_credit`: Sum of all customer credit balances.
- `low_stock_count`: Number of items below minimum threshold.

### `GET /api/dashboard/sales-chart?days=7`
Returns daily aggregated sales and profit points for Recharts visualization.

### `GET /api/dashboard/recent-transactions?limit=5`
Returns latest completed customer invoices.

### `GET /api/dashboard/low-stock?limit=10`
Returns products where `current_stock <= low_stock_threshold`.

### `GET /api/dashboard/summary-ai?lang=kn`
Generates natural language audio brief in Kannada, Malayalam, Hindi, or English.

---

## 4. Products & Inventory (`/api/products` & `/api/inventory`)

- `GET /api/products`: Filterable by `search`, `category`, and `low_stock_only`.
- `POST /api/products`: Create new SKU with purchase price, selling price, and stock.
- `PUT /api/products/{id}`: Edit product details.
- `DELETE /api/products/{id}`: Delete product.
- `POST /api/inventory/adjust`: Atomically adjust stock with `RESTOCK` or `ADJUSTMENT`.
- `GET /api/inventory/history`: Comprehensive audit trail of stock modifications.

---

## 5. Sales & POS Billing (`/api/sales`)

### `POST /api/sales`
Create a customer sale with automatic price lookup, inventory deduction, and optional credit ledger posting.
- **Request Body**:
  ```json
  {
    "customer_id": "optional-uuid",
    "items": [
      {
        "product_id": "product-uuid",
        "quantity": 2.0
      }
    ],
    "discount": 10.0,
    "tax_rate_percent": 5.0,
    "payment_method": "Cash",
    "idempotency_key": "unique-uuid"
  }
  ```
- **Response**: `201 Created` with invoice details and calculated line items.

### `POST /api/sales/{sale_id}/cancel`
Cancels an invoice, reverses customer credit, and automatically restores inventory items via `SALE_CANCEL_RESTORE`.

---

## 6. Customers & Khata Ledger (`/api/customers`)

- `GET /api/customers`: Directory of customers and credit balances.
- `POST /api/customers`: Register new customer with optional opening balance.
- `GET /api/customers/{id}/ledger`: Chronological audit of credit given vs payments.
- `POST /api/customers/{id}/repayments`: Record customer repayment (Cash, UPI, Bank).

---

## 7. Multilingual Voice Assistant (`/api/voice`)

### `POST /api/voice/transcribe`
Uploads raw audio file (`audio/wav`) to Gnani Prisma STT (v3.0).

### `POST /api/voice/command`
Processes text transcription, classifies intent (`GET_TODAYS_SALES`, `UPDATE_STOCK`, `CREATE_SALE`, etc.), executes query or creates two-phase confirmation token.

### `POST /api/voice/confirm`
Executes or cancels pending mutation action using cryptographic confirmation token.

### `POST /api/voice/synthesize`
Generates voice audio using Gnani Timbre TTS (v3.0).

---

## 8. Demo & Competition Data (`/api/demo`)

- `POST /api/demo/seed`: Initializes competition demo dataset.
- `POST /api/demo/reset`: Resets database to baseline state.

