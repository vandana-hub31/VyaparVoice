"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  Layers,
  Plus,
  Minus,
  RefreshCw,
  History,
  AlertTriangle,
  CheckCircle2,
  X
} from "lucide-react";

export default function InventoryPage() {
  const { language } = useAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"current" | "history">("current");
  const [loading, setLoading] = useState(true);

  // Adjustment Modal
  const [adjustingProduct, setAdjustingProduct] = useState<any>(null);
  const [adjType, setAdjType] = useState<"RESTOCK" | "ADJUSTMENT">("RESTOCK");
  const [qtyChange, setQtyChange] = useState("");
  const [reason, setReason] = useState("");

  const t = translations[language] || translations.en;

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === "current") {
        const prods = await api.getProducts();
        setProducts(prods);
      } else {
        const hist = await api.getInventoryHistory(60);
        setHistory(hist);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdjust = (prod: any, type: "RESTOCK" | "ADJUSTMENT") => {
    setAdjustingProduct(prod);
    setAdjType(type);
    setQtyChange("");
    setReason(type === "RESTOCK" ? "Restock from distributor" : "Manual stock correction");
  };

  const handleSaveAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustingProduct || !qtyChange) return;

    try {
      const delta = adjType === "RESTOCK" ? Math.abs(Number(qtyChange)) : Number(qtyChange);
      await api.adjustInventory({
        product_id: adjustingProduct.id,
        quantity_change: delta,
        transaction_type: adjType,
        description: reason
      });

      setAdjustingProduct(null);
      await fetchData();
    } catch (err: any) {
      alert(err?.message || "Failed to adjust stock");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t.inventory}</h1>
          <p className="text-xs text-slate-500">Live stock audit, restock supplies, and trace deductions</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-semibold self-start sm:self-center">
          <button
            onClick={() => setActiveTab("current")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "current" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
            }`}
          >
            Live Stock Levels
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "history" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
            }`}
          >
            Audit History
          </button>
        </div>
      </div>

      {activeTab === "current" ? (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4 text-right">In Stock</th>
                  <th className="py-3 px-4 text-right">Threshold</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Quick Restock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.map((p) => {
                  const isLow = Number(p.current_stock) <= Number(p.low_stock_threshold);
                  return (
                    <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-900">{p.product_name}</td>
                      <td className="py-3 px-4 text-slate-500">{p.category}</td>
                      <td className="py-3 px-4 text-right font-extrabold text-slate-900">
                        {p.current_stock} {p.unit}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-500">
                        {p.low_stock_threshold} {p.unit}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {isLow ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                            <AlertTriangle className="w-3 h-3" />
                            Low Stock
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3" />
                            Adequate
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right space-x-1.5">
                        <button
                          onClick={() => handleOpenAdjust(p, "RESTOCK")}
                          className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-[11px] rounded-lg border border-emerald-200"
                        >
                          + Restock
                        </button>
                        <button
                          onClick={() => handleOpenAdjust(p, "ADJUSTMENT")}
                          className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium text-[11px] rounded-lg border border-slate-200"
                        >
                          Adjust
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Product</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-right">Quantity Change</th>
                  <th className="py-3 px-4">Reason / Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(tx.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900">{tx.product_name}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 font-semibold text-[10px] text-slate-700">
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-extrabold">
                      <span className={Number(tx.quantity) > 0 ? "text-emerald-600" : "text-rose-600"}>
                        {Number(tx.quantity) > 0 ? `+${tx.quantity}` : tx.quantity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{tx.description || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Adjust Stock Modal */}
      {adjustingProduct && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white max-w-sm w-full rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">
                {adjType === "RESTOCK" ? "Restock Inventory" : "Adjust Inventory"}
              </h3>
              <button onClick={() => setAdjustingProduct(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Product: <strong className="text-slate-900">{adjustingProduct.product_name}</strong>
              <br />
              Current Stock: <strong>{adjustingProduct.current_stock} {adjustingProduct.unit}</strong>
            </p>

            <form onSubmit={handleSaveAdjustment} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  {adjType === "RESTOCK" ? "Quantity to Add *" : "Quantity Change (+ or -) *"}
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={qtyChange}
                  onChange={(e) => setQtyChange(e.target.value)}
                  placeholder={adjType === "RESTOCK" ? "e.g. 10" : "e.g. -2 or 5"}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Reason / Reference</label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Distributor crate, damaged, audit"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setAdjustingProduct(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl font-bold"
                >
                  Save Stock
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

