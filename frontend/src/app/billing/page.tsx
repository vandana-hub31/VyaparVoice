"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  Receipt,
  Search,
  Plus,
  Minus,
  Trash2,
  CheckCircle2,
  User,
  CreditCard,
  Percent,
  Printer
} from "lucide-react";

export default function BillingPage() {
  const { business, language } = useAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [cart, setCart] = useState<{ product: any; quantity: number }[]>([]);
  const [discount, setDiscount] = useState("0");
  const [taxPercent, setTaxPercent] = useState("0");
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [loading, setLoading] = useState(false);
  const [lastInvoice, setLastInvoice] = useState<any>(null);

  const t = translations[language] || translations.en;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [prods, custs] = await Promise.all([
        api.getProducts(),
        api.getCustomers()
      ]);
      setProducts(prods);
      setCustomers(custs);
    } catch (err) {
      console.error(err);
    }
  };

  const addToCart = (product: any) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  };

  const updateQuantity = (productId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((item) => {
          if (item.product.id === productId) {
            const newQty = item.quantity + delta;
            return newQty > 0 ? { ...item, quantity: newQty } : null;
          }
          return item;
        })
        .filter(Boolean) as { product: any; quantity: number }[]
    );
  };

  const removeFromCart = (productId: string) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const subtotal = cart.reduce((sum, item) => sum + Number(item.product.selling_price) * item.quantity, 0);
  const discountVal = Number(discount) || 0;
  const taxable = Math.max(0, subtotal - discountVal);
  const taxVal = (taxable * (Number(taxPercent) || 0)) / 100;
  const total = taxable + taxVal;

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cart.length === 0 || loading) return;

    if (paymentMethod === "Credit" && !selectedCustomerId) {
      alert("Please select a customer for Credit billing.");
      return;
    }

    setLoading(true);
    try {
      const salePayload = {
        customer_id: selectedCustomerId || null,
        items: cart.map((i) => ({
          product_id: i.product.id,
          quantity: i.quantity
        })),
        discount: discountVal,
        tax_rate_percent: Number(taxPercent) || 0,
        payment_method: paymentMethod,
        idempotency_key: `pos-${Date.now()}`
      };

      const result = await api.createSale(salePayload);
      setLastInvoice(result);
      setCart([]);
      setDiscount("0");
      setSelectedCustomerId("");
      await loadData();
    } catch (err: any) {
      alert(err?.message || "Failed to complete sale");
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter((p) =>
    p.product_name.toLowerCase().includes(search.toLowerCase()) ||
    (p.category && p.category.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t.billing}</h1>
          <p className="text-xs text-slate-500">Fast counter point-of-sale with real inventory deductions</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Product Selector */}
        <div className="lg:col-span-2 space-y-4">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search product by name or category..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500 shadow-xs"
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[560px] overflow-y-auto pr-1">
            {filteredProducts.map((p) => (
              <button
                key={p.id}
                onClick={() => addToCart(p)}
                disabled={Number(p.current_stock) <= 0}
                className="p-3 bg-white border border-slate-200 hover:border-vyapar-400 rounded-xl text-left shadow-xs transition-all hover:shadow-sm disabled:opacity-40"
              >
                <span className="text-[10px] font-semibold text-vyapar-600 uppercase">{p.category}</span>
                <p className="text-xs font-bold text-slate-900 mt-0.5 line-clamp-1">{p.product_name}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-sm font-extrabold text-slate-900">
                    ₹{Number(p.selling_price).toFixed(2)}
                  </span>
                  <span className={`text-[10px] font-semibold ${
                    Number(p.current_stock) <= Number(p.low_stock_threshold) ? "text-amber-600" : "text-slate-500"
                  }`}>
                    {p.current_stock} {p.unit}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right: Cart & Invoice Checkout */}
        <div className="bg-white p-5 border border-slate-200 rounded-2xl shadow-sm flex flex-col h-full">
          <h2 className="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
            <Receipt className="w-4 h-4 text-vyapar-600" />
            Current Bill ({cart.length} items)
          </h2>

          {/* Cart items */}
          <div className="flex-1 divide-y divide-slate-100 overflow-y-auto max-h-[260px] mb-4">
            {cart.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-10">Cart is empty. Tap products to add.</p>
            ) : (
              cart.map((item) => (
                <div key={item.product.id} className="py-2.5 flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-900 truncate">{item.product.product_name}</p>
                    <p className="text-[10px] text-slate-500">
                      ₹{Number(item.product.selling_price).toFixed(2)} × {item.quantity} = ₹{(Number(item.product.selling_price) * item.quantity).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => updateQuantity(item.product.id, -1)}
                      className="p-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="text-xs font-bold w-5 text-center">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.product.id, 1)}
                      className="p-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => removeFromCart(item.product.id)}
                      className="p-1 text-slate-400 hover:text-red-500 ml-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Checkout Controls */}
          <form onSubmit={handleCheckout} className="space-y-3 pt-3 border-t border-slate-100">
            {/* Customer selector */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Customer (Optional / Required for Credit)</label>
              <select
                value={selectedCustomerId}
                onChange={(e) => setSelectedCustomerId(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:ring-1 focus:ring-vyapar-500"
              >
                <option value="">Walk-in Customer</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.customer_name} (Balance: ₹{Number(c.outstanding_balance).toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            {/* Discount & Tax */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">Discount (₹)</label>
                <input
                  type="number"
                  min="0"
                  value={discount}
                  onChange={(e) => setDiscount(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">Tax (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={taxPercent}
                  onChange={(e) => setTaxPercent(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg"
                />
              </div>
            </div>

            {/* Payment Method */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Payment Method</label>
              <div className="grid grid-cols-4 gap-1">
                {["Cash", "UPI", "Card", "Credit"].map((m) => (
                  <button
                    type="button"
                    key={m}
                    onClick={() => setPaymentMethod(m)}
                    className={`py-1 text-xs font-semibold rounded-lg border transition-all ${
                      paymentMethod === m
                        ? "bg-slate-900 text-white border-slate-900"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            {/* Price Breakdown */}
            <div className="bg-slate-50 p-3 rounded-xl space-y-1 text-xs">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              {discountVal > 0 && (
                <div className="flex justify-between text-emerald-600 font-medium">
                  <span>Discount</span>
                  <span>-₹{discountVal.toFixed(2)}</span>
                </div>
              )}
              {taxVal > 0 && (
                <div className="flex justify-between text-slate-600">
                  <span>Tax ({taxPercent}%)</span>
                  <span>+₹{taxVal.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-extrabold text-slate-900 pt-1 border-t border-slate-200">
                <span>Total Amount</span>
                <span>₹{total.toFixed(2)}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={cart.length === 0 || loading}
              className="w-full py-2.5 bg-vyapar-600 hover:bg-vyapar-700 disabled:opacity-40 text-white font-bold rounded-xl text-sm shadow-md shadow-vyapar-200 flex items-center justify-center gap-1.5 transition-all"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{loading ? "Processing..." : `Complete Bill (₹${total.toFixed(2)})`}</span>
            </button>
          </form>

          {/* Invoice popup preview */}
          {lastInvoice && (
            <div className="mt-4 p-3.5 bg-emerald-50 border border-emerald-300 rounded-xl text-xs text-emerald-900 space-y-2">
              <div className="flex items-center justify-between font-bold">
                <span className="flex items-center gap-1.5 text-emerald-800">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Bill Generated Successfully!
                </span>
                <span className="font-mono bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[11px]">
                  {lastInvoice.invoice_number}
                </span>
              </div>
              <p className="text-[11px] text-emerald-700">
                Total: <strong>₹{Number(lastInvoice.total_amount).toFixed(2)}</strong> • Paid via {lastInvoice.payment_method}
              </p>
              <button
                onClick={() => window.print()}
                className="w-full py-1.5 bg-white border border-emerald-300 hover:bg-emerald-100 text-emerald-800 font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print Counter Receipt</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

