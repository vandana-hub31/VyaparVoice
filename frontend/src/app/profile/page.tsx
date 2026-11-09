"use client";

import React from "react";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import { User, Mail, Phone, Globe, Shield, Calendar, LogOut } from "lucide-react";

export default function ProfilePage() {
  const { user, business, language, logout } = useAuth();
  const t = translations[language] || translations.en;

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t.profile}</h1>
        <p className="text-xs text-slate-500">Your shopkeeper profile and credentials</p>
      </div>

      <div className="bg-white p-6 border border-slate-200 rounded-2xl shadow-xs space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
          <div className="w-16 h-16 rounded-2xl bg-vyapar-600 text-white font-bold text-2xl flex items-center justify-center shadow-md shadow-vyapar-200">
            {user?.full_name?.charAt(0).toUpperCase() || "U"}
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">{user?.full_name}</h2>
            <p className="text-xs text-slate-500">{business?.business_name}</p>
            <span className="inline-block mt-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
              Verified Owner
            </span>
          </div>
        </div>

        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <span className="text-slate-500 flex items-center gap-2">
              <Mail className="w-4 h-4 text-slate-400" />
              Email Address
            </span>
            <span className="font-semibold text-slate-900">{user?.email}</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <span className="text-slate-500 flex items-center gap-2">
              <Phone className="w-4 h-4 text-slate-400" />
              Phone Number
            </span>
            <span className="font-semibold text-slate-900">{user?.phone || "Not configured"}</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <span className="text-slate-500 flex items-center gap-2">
              <Globe className="w-4 h-4 text-slate-400" />
              Preferred Language
            </span>
            <span className="font-semibold text-slate-900 uppercase">{user?.preferred_language || "en"}</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <span className="text-slate-500 flex items-center gap-2">
              <Shield className="w-4 h-4 text-slate-400" />
              Security Role
            </span>
            <span className="font-semibold text-slate-900">Store Administrator</span>
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={logout}
            className="w-full py-2.5 bg-red-50 hover:bg-red-100 text-red-700 font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-colors border border-red-200"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out from Shop Account</span>
          </button>
        </div>
      </div>
    </div>
  );
}
