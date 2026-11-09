"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { translations } from "@/lib/translations";
import {
  TrendingUp,
  Receipt,
  Wallet,
  Users,
  Package,
  AlertTriangle,
  Mic,
  ArrowUpRight,
  Plus,
  RefreshCw,
  Sparkles,
  Volume2
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

export default function DashboardPage() {
  const { user, business, language } = useAuth();
  const [summary, setSummary] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [recentTx, setRecentTx] = useState<any[]>([]);
  const [lowStock, setLowStock] = useState<any[]>([]);
  const [topProducts, setTopProducts] = useState<any[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [chartDays, setChartDays] = useState(7);
  const [loading, setLoading] = useState(true);

  const t = translations[language] || translations.en;

  useEffect(() => {
    fetchDashboardData();
  }, [chartDays, language]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [sumRes, chartRes, txRes, stockRes, topRes, aiRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getSalesChart(chartDays),
        api.getRecentTransactions(5),
        api.getLowStockAlerts(5),
        api.getTopProducts(4),
        api.getAiDailySummary(language)
      ]);

      setSummary(sumRes);
      setChartData(chartRes);
      setRecentTx(txRes);
      setLowStock(stockRes);
      setTopProducts(topRes);
      setAiSummary(aiRes?.summary || "");
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  const playAiSummaryVoice = async () => {
    if (!aiSummary) return;
    try {
      const res = await api.synthesizeSpeech({
        text: aiSummary,
        language
      });
      if (res?.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${res.audio_base64}`);
        audio.play();
      }
    } catch (err) {
      console.error("Audio playback error:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header greeting & quick voice bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <span className="text-xs font-semibold text-vyapar-700 uppercase tracking-wider">
            {business?.business_name || "VyaparVoice Store"}
          </span>
          <h1 className="text-2xl font-bold text-slate-900 mt-0.5">
            {t.welcomeBack}, {user?.full_name?.split(" ")[0] || "Shopkeeper"}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {new Date().toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/billing"
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800 transition-colors shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>{t.billing}</span>
          </Link>

          <Link
            href="/voice"
            className="flex items-center gap-2 px-4 py-2.5 bg-vyapar-600 text-white rounded-xl text-xs font-bold hover:bg-vyapar-700 transition-colors shadow-md shadow-vyapar-200"
          >
            <Mic className="w-4 h-4" />
            <span>{t.quickVoiceAction}</span>
          </Link>
        </div>
      </div>

      {/* AI Daily Business Summary Pill */}
      {aiSummary && (
        <div className="p-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-emerald-600 text-white shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                AI Daily Audio Brief
                <span className="text-[10px] font-normal text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  Verified Postgres Aggregates
                </span>
              </p>
              <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
                {aiSummary}
              </p>
            </div>
          </div>
          <button
            onClick={playAiSummaryVoice}
            className="self-end sm:self-center shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-white border border-emerald-300 text-emerald-800 rounded-xl text-xs font-bold shadow-xs hover:bg-emerald-100 transition-colors"
          >
            <Volume2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Hear Voice Summary</span>
          </button>
        </div>
      )}

      {/* Key Metric KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Today's Sales */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">{t.todaySales}</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900">
              ₹{Number(summary?.today_sales || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <p className="text-[11px] text-slate-500 mt-1">
              {summary?.transaction_count || 0} {t.transactions} recorded
            </p>
          </div>
        </div>

        {/* Estimated Gross Profit */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">{t.grossProfit}</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-blue-700">
              ₹{Number(summary?.estimated_gross_profit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <p className="text-[11px] text-slate-500 mt-1">
              Calculated from cost snapshots
            </p>
          </div>
        </div>

        {/* Today's Expenses */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">{t.todayExpenses}</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900">
              ₹{Number(summary?.today_expenses || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <p className="text-[11px] text-slate-500 mt-1">
              Operating costs & supplies
            </p>
          </div>
        </div>

        {/* Customer Credit Balance */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">{t.outstandingCredit}</span>
            <div className="p-2 rounded-xl bg-rose-50 text-rose-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-rose-700">
              ₹{Number(summary?.outstanding_credit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <p className="text-[11px] text-slate-500 mt-1">
              Total pending repayments
            </p>
          </div>
        </div>
      </div>

      {/* Analytics Chart & Low Stock */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales & Profit Chart */}
        <div className="lg:col-span-2 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-base text-slate-900">Sales & Profit Trend</h2>
              <p className="text-xs text-slate-500">Real transaction figures from PostgreSQL</p>
            </div>
            <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg text-xs">
              <button
                onClick={() => setChartDays(7)}
                className={`px-2.5 py-1 rounded-md font-semibold ${
                  chartDays === 7 ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setChartDays(30)}
                className={`px-2.5 py-1 rounded-md font-semibold ${
                  chartDays === 30 ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
                }`}
              >
                30 Days
              </button>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  formatter={(value: any) => [`₹${Number(value).toLocaleString("en-IN")}`, ""]}
                  contentStyle={{ backgroundColor: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}
                />
                <Area type="monotone" dataKey="sales" name="Sales" stroke="#22c55e" strokeWidth={2} fillOpacity={1} fill="url(#salesGrad)" />
                <Area type="monotone" dataKey="profit" name="Gross Profit" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#profitGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <h2 className="font-bold text-base text-slate-900">{t.lowStock}</h2>
            </div>
            <Link href="/inventory" className="text-xs font-semibold text-vyapar-600 hover:underline">
              View All
            </Link>
          </div>

          <div className="space-y-3 flex-1">
            {lowStock.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">All inventory levels healthy.</p>
            ) : (
              lowStock.map((item) => (
                <div
                  key={item.id}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between"
                >
                  <div>
                    <p className="text-xs font-bold text-slate-900">{item.product_name}</p>
                    <p className="text-[10px] text-slate-500">{item.category}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-extrabold text-amber-600">
                      {item.current_stock} {item.unit}
                    </span>
                    <p className="text-[10px] text-slate-400">Min: {item.low_stock_threshold}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Transactions & Top Selling Products */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-base text-slate-900">Recent Transactions</h2>
            <Link href="/sales" className="text-xs font-semibold text-vyapar-600 hover:underline">
              All Invoices
            </Link>
          </div>

          <div className="divide-y divide-slate-100">
            {recentTx.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No sales recorded yet.</p>
            ) : (
              recentTx.map((tx) => (
                <div key={tx.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-900">{tx.invoice_number}</p>
                    <p className="text-[11px] text-slate-500">{tx.customer_name} • {tx.payment_method}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-slate-900">
                      ₹{Number(tx.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                    <span className={`block text-[10px] font-semibold ${
                      tx.payment_status === "PAID" ? "text-emerald-600" : tx.payment_status === "CANCELLED" ? "text-red-500" : "text-amber-600"
                    }`}>
                      {tx.payment_status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-base text-slate-900">Best-Selling Products</h2>
            <Link href="/products" className="text-xs font-semibold text-vyapar-600 hover:underline">
              Catalog
            </Link>
          </div>

          <div className="divide-y divide-slate-100">
            {topProducts.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No sales data available yet.</p>
            ) : (
              topProducts.map((p, idx) => (
                <div key={p.product_id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center font-bold text-xs text-slate-600">
                      #{idx + 1}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-slate-900">{p.product_name}</p>
                      <p className="text-[11px] text-slate-500">{p.quantity_sold} units sold</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-slate-900">
                      ₹{Number(p.revenue).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                    <p className="text-[10px] text-emerald-600 font-semibold">
                      +₹{Number(p.profit).toFixed(2)} profit
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

