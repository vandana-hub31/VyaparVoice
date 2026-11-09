"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Mic, Lock, Mail, ArrowRight, Zap, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      await login("demo@vyaparvoice.in", "demo12345");
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Failed to load demo account. Please click Reset Demo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-10 p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-sm">
      <div className="text-center mb-6">
        <div className="w-12 h-12 rounded-2xl bg-vyapar-600 text-white flex items-center justify-center mx-auto mb-3 shadow-md shadow-vyapar-200">
          <Mic className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Sign In to VyaparVoice</h1>
        <p className="text-sm text-slate-500 mt-1">Manage your shop with voice commands</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 1-Click Demo Button */}
      <button
        type="button"
        onClick={handleDemoLogin}
        disabled={loading}
        className="w-full mb-6 py-2.5 px-4 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 hover:bg-emerald-100 transition-colors shadow-xs"
      >
        <Zap className="w-4 h-4 text-emerald-600" />
        1-Click Demo Account (Shree Krishna Kirana)
      </button>

      <div className="relative mb-6 text-center">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200"></div>
        </div>
        <span className="relative bg-white px-2 text-xs text-slate-400 uppercase tracking-wider">
          Or sign in with email
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="shopkeeper@example.com"
              className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-vyapar-200 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? "Authenticating..." : "Sign In"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-slate-500">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-semibold text-vyapar-600 hover:underline">
          Register new shop
        </Link>
      </p>
    </div>
  );
}
