"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { translations } from "@/lib/translations";
import {
  Settings,
  Store,
  Globe,
  FileText,
  MapPin,
  RefreshCw,
  CheckCircle2,
  ShieldAlert,
  Server
} from "lucide-react";

export default function SettingsPage() {
  const { business, refreshBusiness, language, setLanguage, seedDemo } = useAuth();
  const [businessName, setBusinessName] = useState(business?.business_name || "");
  const [businessType, setBusinessType] = useState(business?.business_type || "Kirana / Grocery");
  const [gstin, setGstin] = useState(business?.GSTIN || "");
  const [address, setAddress] = useState(business?.address || "");
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const t = translations[language] || translations.en;

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id) return;
    setSaving(true);
    setMessage(null);
    try {
      await api.updateBusiness(business.id, {
        business_name: businessName,
        business_type: businessType,
        GSTIN: gstin || null,
        address: address || null
      });
      await refreshBusiness();
      setMessage("Settings saved successfully!");
    } catch (err: any) {
      alert(err?.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleResetData = async () => {
    if (!confirm("This will reset demo products, customers, sales, and credit back to pristine competition baseline. Proceed?")) {
      return;
    }
    setResetting(true);
    try {
      await seedDemo();
      alert("Demo data successfully reset! Page will reload.");
      window.location.reload();
    } catch (err: any) {
      alert(err?.message || "Failed to reset demo data");
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t.settings}</h1>
        <p className="text-xs text-slate-500">Configure business information, language, and competition demo mode</p>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{message}</span>
        </div>
      )}

      {/* Business Profile Form */}
      <div className="bg-white p-6 border border-slate-200 rounded-2xl shadow-xs">
        <h2 className="font-bold text-base text-slate-900 mb-4 flex items-center gap-2">
          <Store className="w-4 h-4 text-vyapar-600" />
          Business Details
        </h2>

        <form onSubmit={handleSaveSettings} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Business / Shop Name *</label>
            <input
              type="text"
              required
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Store Category</label>
              <select
                value={businessType}
                onChange={(e) => setBusinessType(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
              >
                <option value="Kirana / Grocery">Kirana / Grocery</option>
                <option value="Supermarket / Retail">Supermarket / Retail</option>
                <option value="Dairy & Provisions">Dairy & Provisions</option>
                <option value="General Store">General Store</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">GSTIN Number</label>
              <input
                type="text"
                value={gstin}
                onChange={(e) => setGstin(e.target.value.toUpperCase())}
                placeholder="29AAAAA0000A1Z5"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl font-mono uppercase"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Shop Address</label>
            <textarea
              rows={2}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Malleshwaram, Bengaluru, Karnataka"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 bg-vyapar-600 hover:bg-vyapar-700 text-white font-bold rounded-xl shadow-md shadow-vyapar-200 transition-all"
            >
              {saving ? "Saving Changes..." : "Save Settings"}
            </button>
          </div>
        </form>
      </div>

      {/* Language Preference */}
      <div className="bg-white p-6 border border-slate-200 rounded-2xl shadow-xs">
        <h2 className="font-bold text-base text-slate-900 mb-2 flex items-center gap-2">
          <Globe className="w-4 h-4 text-blue-600" />
          Regional Language Preference
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Select your default language for spoken voice replies and interface labels.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { code: "kn", label: "ಕನ್ನಡ", sub: "Kannada" },
            { code: "ml", label: "മലയാളം", sub: "Malayalam" },
            { code: "hi", label: "हिन्दी", sub: "Hindi" },
            { code: "en", label: "English", sub: "India" }
          ].map((l) => (
            <button
              key={l.code}
              onClick={() => setLanguage(l.code)}
              className={`p-3 rounded-xl border text-center transition-all ${
                language === l.code
                  ? "bg-vyapar-50 border-vyapar-500 text-vyapar-800 shadow-xs"
                  : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
              }`}
            >
              <span className="font-bold text-sm block">{l.label}</span>
              <span className="text-[10px] text-slate-500">{l.sub}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Gnani AI Integration Status */}
      <div className="bg-white p-6 border border-slate-200 rounded-2xl shadow-xs">
        <h2 className="font-bold text-base text-slate-900 mb-2 flex items-center gap-2">
          <Server className="w-4 h-4 text-vyapar-600" />
          Gnani.ai Official API Integration (Challenge Account)
        </h2>
        <p className="text-xs text-slate-500 mb-4 leading-relaxed">
          The competition voice pipeline connects directly to Gnani Prisma STT (<code>https://api.vachana.ai/stt/v3</code>) and Gnani Timbre TTS (<code>https://api.vachana.ai/api/v1/tts/inference</code>).
        </p>

        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-600">Speech-to-Text Model:</span>
            <span className="font-mono text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">prisma-v3.0 (indic-auto)</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-600">Text-to-Speech Model:</span>
            <span className="font-mono text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">timbre-v3.0 (Nalini)</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-600">API Portal:</span>
            <a href="https://app.gnani.ai" target="_blank" rel="noopener noreferrer" className="text-vyapar-600 font-semibold hover:underline">
              https://app.gnani.ai ↗
            </a>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-600">Configured in:</span>
            <span className="font-mono text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">backend/.env (GNANI_API_KEY)</span>
          </div>
        </div>
      </div>

      {/* Competition Demo Mode & Data Reset */}
      <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-6 shadow-xs">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-bold text-base text-emerald-950 flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-700" />
              Competition Demo Mode & Data Reset
            </h2>
            <p className="text-xs text-emerald-800 mt-1 max-w-xl leading-relaxed">
              Resets the database with the verified competition dataset: 25 authentic Indian grocery products, 10 registered customers with khata ledgers, recent sales, and expenses.
            </p>
          </div>

          <button
            onClick={handleResetData}
            disabled={resetting}
            className="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs rounded-xl shadow-md transition-all shrink-0 flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${resetting ? "animate-spin" : ""}`} />
            <span>Reset Demo Data</span>
          </button>
        </div>
      </div>
    </div>
  );
}

