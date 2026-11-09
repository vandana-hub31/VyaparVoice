"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  ShoppingCart,
  Receipt,
  RotateCcw,
  Eye,
  CheckCircle2,
  XCircle,
  FileText,
  Search,
  X
} from "lucide-react";

export default function SalesPage() {
  const { language } = useAuth();
  const [sales, setSales] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSale, setSelectedSale] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const t = translations[language] || translations.en;

  useEffect(() => {
    fetchSales();
  }, []);

  const fetchSales = async () => {
    setLoading(true);
    try {
      const data = await api.getSales();
      setSales(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewSale = async (id: string) => {
    try {
      const detail = await api.getSale(id);
      setSelectedSale(detail);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancelSale = async (id: string) => {
    if (!confirm("Are you sure you want to cancel this sale? Stock will be restored and any credit reversed.")) {
      return;
    }
    setCancellingId(id);
    try {
      await api.cancelSale(id);
      await fetchSales();
      if (selectedSale?.id === id) {
        setSelectedSale(null);
      }
    } catch (err: any) {
      alert(err?.message || "Failed to cancel sale");
    } finally {
      setCancellingId(null);
    }
  };

  const filteredSales = sales.filter((s) =>
    s.invoice_number.toLowerCase().includes(search.toLowerCase()) ||
    (s.customer_name && s.customer_name.toLowerCase().includes(search.toLowerCase())) ||
    s.payment_method.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t.sales}</h1>
          <p className="text-xs text-slate-500">View invoices, track payments, and manage cancellations</p>
        </div>

        <div className="w-full sm:w-64 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search invoice or customer..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-vyapar-500 shadow-xs"
          />
        </div>
      </div>

      {/* Sales Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Date & Time</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredSales.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-400">
                    {loading ? "Loading invoices..." : "No invoices found."}
                  </td>
                </tr>
              ) : (
                filteredSales.map((sale) => (
                  <tr key={sale.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900">{sale.invoice_number}</td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(sale.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      {sale.customer_name || "Walk-in Customer"}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold text-[10px]">
                        {sale.payment_method}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900">
                      ₹{Number(sale.total_amount).toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          sale.payment_status === "PAID"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : sale.payment_status === "CANCELLED"
                            ? "bg-red-50 text-red-700 border border-red-200"
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}
                      >
                        {sale.payment_status === "PAID" ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : sale.payment_status === "CANCELLED" ? (
                          <XCircle className="w-3 h-3" />
                        ) : null}
                        {sale.payment_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-1">
                      <button
                        onClick={() => handleViewSale(sale.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100"
                        title="View Invoice Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {sale.payment_status !== "CANCELLED" && (
                        <button
                          onClick={() => handleCancelSale(sale.id)}
                          disabled={cancellingId === sale.id}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 disabled:opacity-40"
                          title="Cancel & Restore Stock"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sale Detail Modal */}
      {selectedSale && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white max-w-lg w-full rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-vyapar-600" />
                <div>
                  <h3 className="font-bold text-base text-slate-900">{selectedSale.invoice_number}</h3>
                  <p className="text-[11px] text-slate-500">{new Date(selectedSale.created_at).toLocaleString()}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSale(null)}
                className="p-1 text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs space-y-2">
              <p>
                <strong className="text-slate-600">Customer:</strong>{" "}
                <span className="font-semibold text-slate-900">{selectedSale.customer_name || "Walk-in Customer"}</span>
              </p>
              <p>
                <strong className="text-slate-600">Payment:</strong>{" "}
                <span className="font-semibold text-slate-900">{selectedSale.payment_method} ({selectedSale.payment_status})</span>
              </p>
            </div>

            {/* Line items */}
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-[10px] text-slate-500 uppercase">
                  <tr>
                    <th className="p-2.5">Item</th>
                    <th className="p-2.5 text-right">Qty</th>
                    <th className="p-2.5 text-right">Price</th>
                    <th className="p-2.5 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedSale.items?.map((item: any) => (
                    <tr key={item.id}>
                      <td className="p-2.5 font-medium text-slate-900">{item.product_name}</td>
                      <td className="p-2.5 text-right text-slate-600">{item.quantity}</td>
                      <td className="p-2.5 text-right text-slate-600">₹{Number(item.unit_price).toFixed(2)}</td>
                      <td className="p-2.5 text-right font-bold text-slate-900">₹{Number(item.total_amount).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="space-y-1 text-xs pt-2">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span>₹{Number(selectedSale.subtotal).toFixed(2)}</span>
              </div>
              {Number(selectedSale.discount) > 0 && (
                <div className="flex justify-between text-emerald-600">
                  <span>Discount</span>
                  <span>-₹{Number(selectedSale.discount).toFixed(2)}</span>
                </div>
              )}
              {Number(selectedSale.tax) > 0 && (
                <div className="flex justify-between text-slate-600">
                  <span>Tax</span>
                  <span>+₹{Number(selectedSale.tax).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-bold text-slate-900 pt-1.5 border-t border-slate-200">
                <span>Grand Total</span>
                <span>₹{Number(selectedSale.total_amount).toFixed(2)}</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedSale(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

