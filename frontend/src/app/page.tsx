"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Mic, ArrowRight, ShieldCheck, Languages, Zap, CheckCircle2, TrendingUp, Sparkles } from "lucide-react";

export default function LandingPage() {
  const { user, login } = useAuth();

  const handleQuickDemoLogin = async () => {
    await login("demo@vyaparvoice.in", "demo12345");
    window.location.href = "/dashboard";
  };

  return (
    <div className="flex flex-col items-center justify-center py-8 lg:py-16 text-center max-w-4xl mx-auto">
      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-vyapar-50 border border-vyapar-200 text-vyapar-800 text-xs font-semibold mb-6 shadow-sm">
        <Sparkles className="w-3.5 h-3.5 text-vyapar-600" />
        Great Indian AI Internship Challenge 2026 — Gnani.ai
      </div>

      {/* Hero Title */}
      <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15]">
        Your Shop, <br className="hidden sm:inline" />
        <span className="text-vyapar-600 underline decoration-vyapar-300 decoration-wavy">Ready to Speak.</span>
      </h1>

      <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl leading-relaxed">
        VyaparVoice is a voice-first, multilingual business management operating system designed for small Indian shopkeepers. Speak naturally in <strong>Kannada, Malayalam, Hindi, or English</strong> to record sales, track customer credit, and audit stock in real time.
      </p>

      {/* CTAs */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        {user ? (
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-vyapar-600 text-white font-semibold shadow-lg shadow-vyapar-300 hover:bg-vyapar-700 transition-all text-base"
          >
            Go to Shop Dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
        ) : (
          <>
            <button
              onClick={handleQuickDemoLogin}
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-vyapar-600 text-white font-semibold shadow-lg shadow-vyapar-300 hover:bg-vyapar-700 transition-all text-base"
            >
              <Zap className="w-4 h-4" />
              1-Click Live Competition Demo
            </button>
            <Link
              href="/login"
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white text-slate-700 font-semibold border border-slate-300 shadow-sm hover:bg-slate-50 transition-all text-base"
            >
              Sign In
            </Link>
          </>
        )}
        <Link
          href="/voice"
          className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-emerald-50 text-emerald-800 font-semibold border border-emerald-300 hover:bg-emerald-100 transition-all text-base"
        >
          <Mic className="w-4 h-4 text-emerald-600" />
          Try Voice Assistant
        </Link>
      </div>

      {/* Key Feature Cards */}
      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
        <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-vyapar-100 text-vyapar-700 flex items-center justify-center mb-4">
            <Mic className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-slate-900">Gnani Prisma STT</h3>
          <p className="text-sm text-slate-600 mt-2">
            Speak commands like <em>&quot;10 packets milk add karo&quot;</em> or <em>&quot;ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?&quot;</em>. Fast, accurate transcription optimized for Indian regional dialects.
          </p>
        </div>

        <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center mb-4">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-slate-900">Verified Business Actions</h3>
          <p className="text-sm text-slate-600 mt-2">
            No hallucinations or fake data. Every voice command executes verified PostgreSQL transactions with two-phase confirmations for safe inventory updates.
          </p>
        </div>

        <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
          <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center mb-4">
            <Languages className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-slate-900">Gnani Timbre TTS</h3>
          <p className="text-sm text-slate-600 mt-2">
            Hears back vocal answers in your regional language. Natural Indian speech synthesis for daily sales summaries, low-stock warnings, and payment confirmations.
          </p>
        </div>
      </div>

      {/* Supported Languages Banner */}
      <div className="mt-12 w-full p-4 bg-slate-100 border border-slate-200 rounded-xl flex flex-wrap items-center justify-center gap-3 text-xs font-semibold text-slate-700">
        <span className="text-slate-500 font-medium">Supported Languages:</span>
        <span className="px-2.5 py-1 bg-white rounded-md shadow-xs border border-slate-200">ಕನ್ನಡ (Kannada)</span>
        <span className="px-2.5 py-1 bg-white rounded-md shadow-xs border border-slate-200">മലയാളം (Malayalam)</span>
        <span className="px-2.5 py-1 bg-white rounded-md shadow-xs border border-slate-200">हिन्दी (Hindi)</span>
        <span className="px-2.5 py-1 bg-white rounded-md shadow-xs border border-slate-200">English & Hinglish</span>
        <span className="px-2.5 py-1 bg-white rounded-md shadow-xs border border-slate-200">Code-Mixed Dialects</span>
      </div>
    </div>
  );
}

