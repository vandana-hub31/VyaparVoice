"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  Users,
  Phone,
  MapPin,
  Plus,
  CheckCircle2,
  Receipt,
  RotateCcw,
  X
} from "lucide-react";

export default function CustomerLedgerPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [customer, setCustomer] = useState<any>(null);
  const [ledger, setLedger] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRepayModal, setShowRepayModal] = useState(false);

  // Repayment form
  const [repayAmount, setRepayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("Cash");
  const [notes, setNotes] = useState("Customer repayment");

  useEffect(() => {
    if (id) {
      loadCustomerAndLedger();
    }
  }, [id]);

  const loadCustomerAndLedger = async () => {
    setLoading(true);
    try {
      const [c, l] = await Promise.all([
        api.getCustomer(id),
        api.getCustomerLedger(id)
      ]);
      setCustomer(c);
      setLedger(l);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordRepayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repayAmount || Number(repayAmount) <= 0) return;

    try {
      await api.recordRepayment(id, {
        amount: Number(repayAmount),
        payment_method: payMethod,
        description: notes
      });

      setShowRepayModal(false);
      setRepayAmount("");
      await loadCustomerAndLedger();
    } catch (err: any) {
      alert(err?.message || "Failed to record repayment");
    }
  };

  if (loading && !customer) {
    return <div className="text-center py-20 text-xs text-slate-500">Loading ledger...</div>;
  }

  if (!customer) {
    return <div className="text-center py-20 text-xs text-slate-500">Customer not found.</div>;
  }

  const due = Number(customer.outstanding_balance);

  return (
    <div className="space-y-6">
      <button
        onClick={() => router.push("/customers")}
        className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to All Customers</span>
      </button>

      {/* Customer Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-vyapar-700 uppercase tracking-wider">
            Customer Credit Account
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900 mt-0.5">{customer.customer_name}</h1>
          <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-slate-500">
            {customer.phone && (
              <span className="flex items-center gap-1">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                {customer.phone}
              </span>
            )}
            {customer.address && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                {customer.address}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Current Balance Due</span>
            <span className={`text-2xl font-black ${due > 0 ? "text-rose-600" : "text-emerald-600"}`}>
              ₹{due.toFixed(2)}
            </span>
          </div>

          <button
            onClick={() => setShowRepayModal(true)}
            className="px-4 py-2.5 bg-vyapar-600 hover:bg-vyapar-700 text-white font-bold text-xs rounded-xl shadow-md shadow-vyapar-200 transition-all flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Record Repayment</span>
          </button>
        </div>
      </div>

      {/* Khata Ledger History */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-sm text-slate-900">Transaction History & Ledger</h2>
          <span className="text-xs text-slate-400">{ledger.length} entries recorded</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-200 font-semibold">
              <tr>
                <th className="py-3 px-4">Date & Time</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Notes / Invoice</th>
                <th className="py-3 px-4 text-right">Credit Given</th>
                <th className="py-3 px-4 text-right">Repaid Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {ledger.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-10 text-slate-400">
                    No credit transactions yet.
                  </td>
                </tr>
              ) : (
                ledger.map((tx) => {
                  const isCredit = tx.transaction_type === "CREDIT_GIVEN";
                  return (
                    <tr key={tx.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 text-slate-500">
                        {new Date(tx.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-md font-semibold text-[10px] ${
                            isCredit ? "bg-rose-50 text-rose-700 border border-rose-200" : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          }`}
                        >
                          {isCredit ? "Credit Given (Udhaar)" : "Repayment (Jama)"}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-800">{tx.description || "-"}</td>
                      <td className="py-3 px-4 text-right font-extrabold text-rose-600">
                        {isCredit ? `₹${Number(tx.amount).toFixed(2)}` : "-"}
                      </td>
                      <td className="py-3 px-4 text-right font-extrabold text-emerald-600">
                        {!isCredit ? `₹${Number(tx.amount).toFixed(2)}` : "-"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Record Repayment Modal */}
      {showRepayModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white max-w-sm w-full rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">Record Customer Repayment</h3>
              <button onClick={() => setShowRepayModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Customer: <strong className="text-slate-900">{customer.customer_name}</strong>
              <br />
              Outstanding: <strong className="text-rose-600">₹{due.toFixed(2)}</strong>
            </p>

            <form onSubmit={handleRecordRepayment} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Repayment Amount (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  max={due > 0 ? due : undefined}
                  value={repayAmount}
                  onChange={(e) => setRepayAmount(e.target.value)}
                  placeholder="e.g. 500.00"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Payment Method</label>
                <select
                  value={payMethod}
                  onChange={(e) => setPayMethod(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                >
                  <option value="Cash">Cash</option>
                  <option value="UPI">UPI / GPay / PhonePe</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Notes or transaction ID"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowRepayModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl font-bold"
                >
                  Confirm Repayment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
