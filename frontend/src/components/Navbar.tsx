"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import { Mic, Globe, Store, LogOut } from "lucide-react";

export default function Navbar() {
  const { user, business, language, setLanguage, logout } = useAuth();

  const t = translations[language] || translations.en;

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-vyapar-600 flex items-center justify-center text-white shadow-md shadow-vyapar-200">
              <Mic className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight text-slate-900 flex items-center gap-1.5">
                Vyapar<span className="text-vyapar-600">Voice</span>
              </span>
              <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider hidden sm:block">
                Powered by Gnani.ai
              </p>
            </div>
          </Link>

          {business && (
            <div className="hidden md:flex items-center gap-1.5 ml-4 px-2.5 py-1 bg-slate-100 rounded-lg text-xs font-medium text-slate-700">
              <Store className="w-3.5 h-3.5 text-slate-500" />
              <span className="truncate max-w-[180px]">{business.business_name}</span>
            </div>
          )}
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Language Switcher */}
          <div className="relative flex items-center">
            <Globe className="w-4 h-4 text-slate-500 absolute left-2 pointer-events-none" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="pl-7 pr-3 py-1.5 text-xs font-semibold bg-slate-50 border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-vyapar-500 cursor-pointer"
            >
              <option value="en">English</option>
              <option value="kn">ಕನ್ನಡ (Kannada)</option>
              <option value="ml">മലയാളം (Malayalam)</option>
              <option value="hi">हिन्दी (Hindi)</option>
            </select>
          </div>

          {/* Voice Assistant Shortcut Button */}
          <Link
            href="/voice"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-vyapar-600 text-white hover:bg-vyapar-700 shadow-sm transition-all"
          >
            <Mic className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t.voiceAssistant}</span>
          </Link>

          {/* User profile / Logout */}
          {user ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <Link
                href="/profile"
                className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 hover:bg-slate-300 font-semibold text-xs"
                title={user.full_name}
              >
                {user.full_name.charAt(0).toUpperCase()}
              </Link>
              <button
                onClick={logout}
                title={t.logout}
                className="p-1.5 text-slate-500 hover:text-red-600 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="text-xs font-semibold px-3 py-1.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

