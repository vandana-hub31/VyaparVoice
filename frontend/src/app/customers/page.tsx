"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  Users,
  Plus,
  Search,
  Phone,
  MapPin,
  ArrowRight,
  CreditCard,
  CheckCircle2,
  X
} from "lucide-react";

export default function CustomersPage() {
  const { language } = useAuth();
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [hasBalanceOnly, setHasBalanceOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [openingBalance, setOpeningBalance] = useState("0");

  const t = translations[language] || translations.en;

  useEffect(() => {
    fetchCustomers();
  }, [hasBalanceOnly]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const data = await api.getCustomers(undefined, hasBalanceOnly);
      setCustomers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      await api.createCustomer({
        customer_name: name.trim(),
        phone: phone.trim() || null,
        address: address.trim() || null,
        initial_balance: Number(openingBalance) || 0
      });

      setShowAddModal(false);
      setName("");
      setPhone("");
      setAddress("");
      setOpeningBalance("0");
      await fetchCustomers();
    } catch (err: any) {
      alert(err?.message || "Failed to add customer");
    }
  };

  const filtered = customers.filter((c) =>
    c.customer_name.toLowerCase().includes(search.toLowerCase()) ||
    (c.phone && c.phone.includes(search))
  );

  const totalCreditDue = customers.reduce((sum, c) => sum + Number(c.outstanding_balance), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t.customers}</h1>
          <p className="text-xs text-slate-500">Track regular customers, udhaari balances, and repayment ledgers</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl text-xs font-bold shadow-md shadow-vyapar-200 transition-all self-start sm:self-center"
        >
          <Plus className="w-4 h-4" />
          <span>{t.addCustomer}</span>
        </button>
      </div>

      {/* Credit Summary Pill */}
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-rose-700 uppercase tracking-wider">Total Customer Credit Due</span>
          <p className="text-2xl font-bold text-rose-900 mt-0.5">
            ₹{totalCreditDue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </p>
        </div>
        <button
          onClick={() => setHasBalanceOnly(!hasBalanceOnly)}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-colors ${
            hasBalanceOnly ? "bg-rose-600 text-white border-rose-700" : "bg-white text-rose-800 border-rose-300"
          }`}
        >
          {hasBalanceOnly ? "Showing Debtors Only" : "Filter Debtors Only"}
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search customer by name or phone number..."
          className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-vyapar-500 shadow-xs"
        />
      </div>

      {/* Customers List Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((c) => {
          const hasBalance = Number(c.outstanding_balance) > 0;
          return (
            <div
              key={c.id}
              className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-base text-slate-900">{c.customer_name}</h3>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                      hasBalance
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    }`}
                  >
                    {hasBalance ? `Due: ₹${Number(c.outstanding_balance).toFixed(2)}` : "Settled"}
                  </span>
                </div>

                <div className="mt-3 space-y-1 text-xs text-slate-500">
                  {c.phone && (
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{c.phone}</span>
                    </div>
                  )}
                  {c.address && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">{c.address}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                <Link
                  href={`/customers/${c.id}`}
                  className="text-xs font-bold text-vyapar-700 hover:text-vyapar-900 flex items-center gap-1"
                >
                  <span>View Khata / Ledger</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Customer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white max-w-sm w-full rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">Add Customer to Khata</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddCustomer} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Customer Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="9876543210"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Address / Street</label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="12th Cross, Malleshwaram"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Opening Udhaari Balance (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={openingBalance}
                  onChange={(e) => setOpeningBalance(e.target.value)}
                  placeholder="0.00"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl font-bold"
                >
                  Save Customer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

