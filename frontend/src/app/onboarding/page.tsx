"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Store, MapPin, FileText, CheckCircle2, ArrowRight } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { business, refreshBusiness } = useAuth();
  const [businessName, setBusinessName] = useState(business?.business_name || "");
  const [businessType, setBusinessType] = useState(business?.business_type || "Kirana / Grocery");
  const [gstin, setGstin] = useState(business?.GSTIN || "");
  const [address, setAddress] = useState(business?.address || "");
  const [currency, setCurrency] = useState("INR");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (business?.id) {
        await api.updateBusiness(business.id, {
          business_name: businessName,
          business_type: businessType,
          GSTIN: gstin || null,
          address: address || null,
          currency,
          timezone
        });
      } else {
        await api.createBusiness({
          business_name: businessName,
          business_type: businessType,
          GSTIN: gstin || null,
          address: address || null,
          currency,
          timezone
        });
      }
      await refreshBusiness();
      router.push("/dashboard");
    } catch (err) {
      console.error("Onboarding failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto my-6 p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-sm">
      <div className="mb-6">
        <span className="text-xs font-bold uppercase tracking-wider text-vyapar-600 bg-vyapar-50 px-2.5 py-1 rounded-md">
          Step 2 of 2
        </span>
        <h1 className="text-2xl font-bold text-slate-900 mt-2">Setup Your Business Profile</h1>
        <p className="text-sm text-slate-500">Configure your store settings, tax ID, and local preferences.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Business / Shop Name *</label>
          <div className="relative">
            <Store className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              required
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="e.g. Mahalakshmi Kirana & Provisions"
              className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Business Type</label>
            <select
              value={businessType}
              onChange={(e) => setBusinessType(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500"
            >
              <option value="Kirana / Grocery">Kirana / Grocery</option>
              <option value="Supermarket / Retail">Supermarket / Retail</option>
              <option value="Dairy / Bakery">Dairy / Bakery</option>
              <option value="Vegetable & Fruits">Vegetable & Fruits</option>
              <option value="Wholesale Provisions">Wholesale Provisions</option>
              <option value="General Store">General Store</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">GSTIN (Optional)</label>
            <div className="relative">
              <FileText className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={gstin}
                onChange={(e) => setGstin(e.target.value.toUpperCase())}
                placeholder="29AAAAA0000A1Z5"
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500 uppercase"
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
            <input
              type="text"
              disabled
              value={`${currency} (Indian Rupee - ₹)`}
              className="w-full px-3 py-2 text-sm bg-slate-100 border border-slate-300 rounded-xl text-slate-600 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Timezone</label>
            <input
              type="text"
              disabled
              value={`${timezone} (IST)`}
              className="w-full px-3 py-2 text-sm bg-slate-100 border border-slate-300 rounded-xl text-slate-600 cursor-not-allowed"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Shop Address</label>
          <div className="relative">
            <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <textarea
              rows={2}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Shop number, street, city, pincode"
              className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-4 py-3 px-4 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-vyapar-200 transition-all flex items-center justify-center gap-2"
        >
          {loading ? "Saving Setup..." : "Launch Store Dashboard"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
