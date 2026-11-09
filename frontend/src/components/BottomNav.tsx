"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import { LayoutDashboard, Receipt, Mic, Users, Menu } from "lucide-react";

export default function BottomNav() {
  const pathname = usePathname();
  const { language } = useAuth();
  const t = translations[language] || translations.en;

  const items = [
    { href: "/dashboard", label: t.dashboard, icon: LayoutDashboard },
    { href: "/billing", label: t.billing, icon: Receipt },
    { href: "/voice", label: t.voiceAssistant, icon: Mic, isCenter: true },
    { href: "/customers", label: t.customers, icon: Users },
    { href: "/settings", label: t.settings, icon: Menu },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-lg px-2 py-1.5 flex items-center justify-around">
      {items.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        if (item.isCenter) {
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex flex-col items-center -mt-6 group"
            >
              <div className="w-14 h-14 rounded-full bg-vyapar-600 border-4 border-white flex items-center justify-center text-white shadow-lg shadow-vyapar-400 recording-pulse">
                <Mic className="w-7 h-7" />
              </div>
              <span className="text-[10px] font-bold text-vyapar-700 mt-1">
                {item.label}
              </span>
            </Link>
          );
        }

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center py-1 px-2 rounded-lg transition-colors ${
              isActive ? "text-vyapar-600 font-bold" : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="text-[10px] mt-0.5 truncate max-w-[60px]">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

