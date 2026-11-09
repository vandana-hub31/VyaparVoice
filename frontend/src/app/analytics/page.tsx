"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  BarChart3,
  TrendingUp,
  Receipt,
  Wallet,
  Package,
  Layers,
  Users
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";

export default function AnalyticsPage() {
  const { language } = useAuth();
  const [dailyData, setDailyData] = useState<any[]>([]);
  const [topProducts, setTopProducts] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [timeframe, setTimeframe] = useState<"daily" | "weekly" | "monthly">("daily");
  const [loading, setLoading] = useState(true);

  const t = translations[language] || translations.en;

  useEffect(() => {
    loadAnalytics();
  }, [timeframe]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      let chartPromise;
      if (timeframe === "daily") {
        chartPromise = api.getDailyAnalytics();
      } else if (timeframe === "weekly") {
        chartPromise = api.getWeeklyAnalytics();
      } else {
        chartPromise = api.getMonthlyAnalytics();
      }

      const [chart, top, sum] = await Promise.all([
        chartPromise,
        api.getTopProducts(8),
        api.getDashboardSummary()
      ]);

      setDailyData(chart);
      setTopProducts(top);
      setSummary(sum);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const netOperatingProfit = Number(summary?.estimated_gross_profit || 0) - Number(summary?.today_expenses || 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t.analytics}</h1>
          <p className="text-xs text-slate-500">Audited financial metrics and revenue vs gross profit derived from PostgreSQL</p>
        </div>

        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-semibold self-start sm:self-center">
          <button
            onClick={() => setTimeframe("daily")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              timeframe === "daily" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => setTimeframe("weekly")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              timeframe === "weekly" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
            }`}
          >
            30 Days
          </button>
          <button
            onClick={() => setTimeframe("monthly")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              timeframe === "monthly" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"
            }`}
          >
            90 Days
          </button>
        </div>
      </div>

      {/* Financial Health Definitions Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Gross Sales Revenue</span>
          <p className="text-2xl font-black text-slate-900 mt-1">
            ₹{Number(summary?.today_sales || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Total revenue collected from invoices</p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Estimated Gross Profit</span>
          <p className="text-2xl font-black text-blue-700 mt-1">
            ₹{Number(summary?.estimated_gross_profit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Calculated from purchase cost snapshots at time of sale</p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">Today&apos;s Net Cashflow</span>
          <p className="text-2xl font-black text-emerald-700 mt-1">
            ₹{netOperatingProfit.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Gross profit minus recorded expenses (₹{Number(summary?.today_expenses || 0).toFixed(2)})</p>
        </div>
      </div>

      {/* Bar Chart: Sales Revenue vs Gross Profit */}
      <div className="bg-white p-5 border border-slate-200 rounded-2xl shadow-xs">
        <div className="mb-4">
          <h2 className="font-bold text-base text-slate-900">Sales vs Gross Profit Comparison</h2>
          <p className="text-xs text-slate-500">Notice that gross profit is strictly separated from sales revenue</p>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dailyData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
              <Tooltip
                formatter={(value: any) => [`₹${Number(value).toLocaleString("en-IN")}`, ""]}
                contentStyle={{ backgroundColor: "#ffffff", borderRadius: "12px", border: "1px solid #e2e8f0" }}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              <Bar dataKey="sales" name="Sales Revenue" fill="#16a34a" radius={[4, 4, 0, 0]} />
              <Bar dataKey="profit" name="Gross Profit" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Best-Selling Products Performance Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-sm text-slate-900">Product Profitability Breakdown</h2>
          <span className="text-xs text-slate-400">Ranked by revenue</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-200 font-semibold">
              <tr>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4 text-right">Units Sold</th>
                <th className="py-3 px-4 text-right">Total Revenue</th>
                <th className="py-3 px-4 text-right">Gross Profit</th>
                <th className="py-3 px-4 text-right">Profit Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {topProducts.map((p) => {
                const rev = Number(p.revenue);
                const prof = Number(p.profit);
                const margin = rev > 0 ? ((prof / rev) * 100).toFixed(1) : "0.0";
                return (
                  <tr key={p.product_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900">{p.product_name}</td>
                    <td className="py-3 px-4 text-right text-slate-600 font-semibold">{p.quantity_sold}</td>
                    <td className="py-3 px-4 text-right font-extrabold text-slate-900">
                      ₹{rev.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-extrabold text-blue-600">
                      +₹{prof.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-600">
                      {margin}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
