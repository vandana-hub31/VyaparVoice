"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  LayoutDashboard,
  Mic,
  Receipt,
  ShoppingCart,
  Package,
  Layers,
  Users,
  Wallet,
  BarChart3,
  Settings
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { language } = useAuth();
  const t = translations[language] || translations.en;

  const links = [
    { href: "/dashboard", label: t.dashboard, icon: LayoutDashboard },
    { href: "/voice", label: t.voiceAssistant, icon: Mic, highlight: true },
    { href: "/billing", label: t.billing, icon: Receipt },
    { href: "/sales", label: t.sales, icon: ShoppingCart },
    { href: "/products", label: t.products, icon: Package },
    { href: "/inventory", label: t.inventory, icon: Layers },
    { href: "/customers", label: t.customers, icon: Users },
    { href: "/expenses", label: t.expenses, icon: Wallet },
    { href: "/analytics", label: t.analytics, icon: BarChart3 },
    { href: "/settings", label: t.settings, icon: Settings },
  ];

  return (
    <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-4rem)] p-4">
      <nav className="space-y-1.5 flex-1">
        {links.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          if (item.highlight) {
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-semibold text-sm transition-all ${
                  isActive
                    ? "bg-vyapar-600 text-white shadow-md shadow-vyapar-200"
                    : "bg-vyapar-50 text-vyapar-800 hover:bg-vyapar-100 border border-vyapar-200"
                }`}
              >
                <div className={`p-1.5 rounded-lg ${isActive ? "bg-vyapar-700" : "bg-vyapar-200"}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span>{item.label}</span>
                <span className="ml-auto flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-vyapar-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-vyapar-500"></span>
                </span>
              </Link>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? "bg-slate-100 text-slate-900 font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-vyapar-600" : "text-slate-400"}`} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Multilingual Assistant Badge */}
      <div className="mt-auto p-3 bg-slate-50 border border-slate-200 rounded-xl">
        <p className="text-[11px] font-semibold text-slate-700">Multilingual Assistant</p>
        <p className="text-[10px] text-slate-500 mt-0.5">Kannada • Malayalam • Hindi • English</p>
      </div>
    </aside>
  );
}

