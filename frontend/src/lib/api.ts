const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = "ApiError";
  }
}

export async function apiFetch<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("vyapar_token") : null;
  const businessId = typeof window !== "undefined" ? localStorage.getItem("vyapar_business_id") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (businessId) {
    headers["X-Business-ID"] = businessId;
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401 && typeof window !== "undefined") {
    // If not on login or register, redirect
    if (!window.location.pathname.includes("/login") && !window.location.pathname.includes("/register")) {
      localStorage.removeItem("vyapar_token");
      localStorage.removeItem("vyapar_user");
      window.location.href = "/login";
    }
  }

  const contentType = response.headers.get("content-type");
  let data: any = null;
  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMsg = data?.detail || response.statusText || "An API error occurred";
    throw new ApiError(response.status, errorMsg, data);
  }

  return data as T;
}

export const api = {
  // Auth
  register: (body: any) => apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: any) => apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  getMe: () => apiFetch("/api/auth/me"),

  // Businesses
  getBusinesses: () => apiFetch("/api/businesses"),
  getCurrentBusiness: () => apiFetch("/api/businesses/current"),
  createBusiness: (body: any) => apiFetch("/api/businesses", { method: "POST", body: JSON.stringify(body) }),
  updateBusiness: (id: string, body: any) => apiFetch(`/api/businesses/${id}`, { method: "PUT", body: JSON.stringify(body) }),

  // Dashboard
  getDashboardSummary: () => apiFetch("/api/dashboard/summary"),
  getSalesChart: (days = 7) => apiFetch(`/api/dashboard/sales-chart?days=${days}`),
  getRecentTransactions: (limit = 5) => apiFetch(`/api/dashboard/recent-transactions?limit=${limit}`),
  getLowStockAlerts: (limit = 10) => apiFetch(`/api/dashboard/low-stock?limit=${limit}`),
  getAiDailySummary: (lang?: string) => apiFetch(`/api/dashboard/summary-ai${lang ? `?lang=${lang}` : ""}`),

  // Products & Inventory
  getProducts: (params?: { search?: string; category?: string; low_stock_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append("search", params.search);
    if (params?.category) searchParams.append("category", params.category);
    if (params?.low_stock_only) searchParams.append("low_stock_only", "true");
    const qs = searchParams.toString();
    return apiFetch(`/api/products${qs ? `?${qs}` : ""}`);
  },
  getProduct: (id: string) => apiFetch(`/api/products/${id}`),
  createProduct: (body: any) => apiFetch("/api/products", { method: "POST", body: JSON.stringify(body) }),
  updateProduct: (id: string, body: any) => apiFetch(`/api/products/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteProduct: (id: string) => apiFetch(`/api/products/${id}`, { method: "DELETE" }),
  adjustInventory: (body: any) => apiFetch("/api/inventory/adjust", { method: "POST", body: JSON.stringify(body) }),
  getInventoryHistory: (limit = 50) => apiFetch(`/api/inventory/history?limit=${limit}`),

  // Sales
  getSales: (customerId?: string, limit = 50) => {
    const qs = customerId ? `?customer_id=${customerId}&limit=${limit}` : `?limit=${limit}`;
    return apiFetch(`/api/sales${qs}`);
  },
  getSale: (id: string) => apiFetch(`/api/sales/${id}`),
  createSale: (body: any) => apiFetch("/api/sales", { method: "POST", body: JSON.stringify(body) }),
  cancelSale: (id: string) => apiFetch(`/api/sales/${id}/cancel`, { method: "POST" }),

  // Customers & Ledger
  getCustomers: (search?: string, hasBalanceOnly?: boolean) => {
    const sp = new URLSearchParams();
    if (search) sp.append("search", search);
    if (hasBalanceOnly) sp.append("has_balance_only", "true");
    const qs = sp.toString();
    return apiFetch(`/api/customers${qs ? `?${qs}` : ""}`);
  },
  getCustomer: (id: string) => apiFetch(`/api/customers/${id}`),
  createCustomer: (body: any) => apiFetch("/api/customers", { method: "POST", body: JSON.stringify(body) }),
  updateCustomer: (id: string, body: any) => apiFetch(`/api/customers/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  getCustomerLedger: (id: string) => apiFetch(`/api/customers/${id}/ledger`),
  recordRepayment: (id: string, body: any) => apiFetch(`/api/customers/${id}/repayments`, { method: "POST", body: JSON.stringify(body) }),

  // Expenses
  getExpenses: (category?: string) => apiFetch(`/api/expenses${category ? `?category=${category}` : ""}`),
  createExpense: (body: any) => apiFetch("/api/expenses", { method: "POST", body: JSON.stringify(body) }),
  deleteExpense: (id: string) => apiFetch(`/api/expenses/${id}`, { method: "DELETE" }),
  getExpenseSummary: () => apiFetch("/api/expenses/summary"),

  // Analytics
  getDailyAnalytics: () => apiFetch("/api/analytics/daily"),
  getWeeklyAnalytics: () => apiFetch("/api/analytics/weekly"),
  getMonthlyAnalytics: () => apiFetch("/api/analytics/monthly"),
  getTopProducts: (limit = 5) => apiFetch(`/api/analytics/top-products?limit=${limit}`),

  // Voice Assistant
  getGnaniStatus: () => apiFetch("/api/voice/gnani/status"),
  transcribeAudio: (formData: FormData) => apiFetch("/api/voice/transcribe", { method: "POST", body: formData }),
  processVoiceCommand: (body: { transcription: string; language?: string; idempotency_key?: string }) =>
    apiFetch("/api/voice/command", { method: "POST", body: JSON.stringify(body) }),
  confirmVoiceAction: (body: { confirmation_token: string; confirmed: boolean }) =>
    apiFetch("/api/voice/confirm", { method: "POST", body: JSON.stringify(body) }),
  synthesizeSpeech: (body: { text: string; language?: string; voice?: string; speed?: number }) =>
    apiFetch("/api/voice/synthesize", { method: "POST", body: JSON.stringify(body) }),
  getVoiceHistory: (limit = 20) => apiFetch(`/api/voice/history?limit=${limit}`),

  // Demo
  seedDemoData: () => apiFetch("/api/demo/seed", { method: "POST" }),
  resetDemoData: () => apiFetch("/api/demo/reset", { method: "POST" }),
};

