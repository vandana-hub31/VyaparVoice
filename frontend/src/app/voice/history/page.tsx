"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { translations } from "@/lib/translations";
import {
  MessageSquare,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Languages,
  Mic,
  ArrowLeft,
  Filter,
} from "lucide-react";

interface VoiceHistoryItem {
  id: string;
  transcription: string;
  detected_intent: string;
  execution_status: string;
  response_text: string;
  input_language: string;
  created_at: string;
}

type FilterStatus = "ALL" | "SUCCESS" | "FAILED" | "PENDING_CONFIRMATION";

const LANGUAGE_LABELS: Record<string, string> = {
  kn: "Kannada",
  ml: "Malayalam",
  hi: "Hindi",
  ta: "Tamil",
  en: "English",
};

const STATUS_CONFIG: Record<
  string,
  { label: string; badgeClass: string; icon: React.ReactNode }
> = {
  SUCCESS: {
    label: "Success",
    badgeClass:
      "bg-emerald-50 text-emerald-800 border border-emerald-300",
    icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />,
  },
  FAILED: {
    label: "Failed",
    badgeClass: "bg-red-50 text-red-800 border border-red-300",
    icon: <XCircle className="w-3.5 h-3.5 text-red-600" />,
  },
  PENDING_CONFIRMATION: {
    label: "Pending",
    badgeClass: "bg-amber-50 text-amber-800 border border-amber-300",
    icon: <AlertCircle className="w-3.5 h-3.5 text-amber-600" />,
  },
  CANCELLED: {
    label: "Cancelled",
    badgeClass: "bg-slate-100 text-slate-700 border border-slate-300",
    icon: <XCircle className="w-3.5 h-3.5 text-slate-500" />,
  },
};

function getStatusConfig(status: string) {
  return (
    STATUS_CONFIG[status] ?? {
      label: status,
      badgeClass: "bg-slate-100 text-slate-700 border border-slate-300",
      icon: <Clock className="w-3.5 h-3.5 text-slate-500" />,
    }
  );
}

function getLanguageBadge(lang: string) {
  const name = LANGUAGE_LABELS[lang] ?? lang?.toUpperCase();
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-vyapar-50 text-vyapar-700 border border-vyapar-200 text-[11px] font-semibold">
      <Languages className="w-3 h-3" />
      {name}
    </span>
  );
}

function formatRelativeTime(dateStr: string) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

const FILTER_BUTTONS: { label: string; value: FilterStatus }[] = [
  { label: "All", value: "ALL" },
  { label: "Success", value: "SUCCESS" },
  { label: "Failed", value: "FAILED" },
  { label: "Pending", value: "PENDING_CONFIRMATION" },
];

export default function VoiceHistoryPage() {
  const { language } = useAuth();
  const t = translations[language] || translations.en;

  const [history, setHistory] = useState<VoiceHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<FilterStatus>("ALL");

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getVoiceHistory(50);
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load voice history:", err);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const filtered =
    activeFilter === "ALL"
      ? history
      : history.filter((item) => item.execution_status === activeFilter);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/voice"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-vyapar-600 hover:text-vyapar-800 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Voice Assistant
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Mic className="w-6 h-6 text-vyapar-600" />
            Voice Interaction History
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Complete log of all voice commands processed by VyaparVoice AI
          </p>
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-semibold self-start sm:self-center border border-slate-200">
          <Filter className="w-3.5 h-3.5 text-slate-500 ml-1" />
          {FILTER_BUTTONS.map((btn) => (
            <button
              key={btn.value}
              onClick={() => setActiveFilter(btn.value)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeFilter === btn.value
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-xs p-12 flex flex-col items-center gap-3">
          <span className="w-8 h-8 rounded-full border-2 border-vyapar-500 border-t-transparent animate-spin" />
          <p className="text-sm text-slate-500 font-medium">
            Loading voice history...
          </p>
        </div>
      )}

      {/* Empty State */}
      {!loading && filtered.length === 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-xs p-12 flex flex-col items-center gap-4 text-center">
          <div className="w-16 h-16 rounded-full bg-vyapar-50 border border-vyapar-200 flex items-center justify-center">
            <MessageSquare className="w-8 h-8 text-vyapar-400" />
          </div>
          <div>
            <p className="text-base font-semibold text-slate-700">
              {activeFilter === "ALL"
                ? "No voice interactions recorded yet. Try the Voice Assistant!"
                : `No ${activeFilter.toLowerCase().replace("_", " ")} interactions found.`}
            </p>
            {activeFilter === "ALL" && (
              <p className="text-xs text-slate-400 mt-1">
                Your voice commands will appear here after you use the assistant.
              </p>
            )}
          </div>
          {activeFilter === "ALL" && (
            <Link
              href="/voice"
              className="mt-1 inline-flex items-center gap-2 px-4 py-2.5 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors"
            >
              <Mic className="w-4 h-4" />
              Open Voice Assistant
            </Link>
          )}
        </div>
      )}

      {/* History Cards */}
      {!loading && filtered.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-slate-400 font-medium px-1">
            Showing {filtered.length} interaction{filtered.length !== 1 ? "s" : ""}
          </p>

          {filtered.map((item) => {
            const statusCfg = getStatusConfig(item.execution_status);
            return (
              <div
                key={item.id}
                className="bg-white border border-slate-200 rounded-2xl shadow-xs hover:shadow-sm hover:border-slate-300 transition-all p-5"
              >
                {/* Top row: intent badge + language + time */}
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {/* Status badge */}
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold ${statusCfg.badgeClass}`}
                  >
                    {statusCfg.icon}
                    {statusCfg.label}
                  </span>

                  {/* Intent badge */}
                  {item.detected_intent && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-semibold">
                      <MessageSquare className="w-3 h-3" />
                      {item.detected_intent.replace(/_/g, " ")}
                    </span>
                  )}

                  {/* Language badge */}
                  {item.input_language && getLanguageBadge(item.input_language)}

                  {/* Time — pushed to right on wider screens */}
                  <span className="ml-auto flex items-center gap-1 text-[11px] text-slate-400 font-medium shrink-0">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(item.created_at)}
                  </span>
                </div>

                {/* Transcription */}
                <div className="mb-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    You said
                  </span>
                  <p className="text-sm font-semibold text-slate-900 mt-0.5 leading-snug">
                    &ldquo;{item.transcription}&rdquo;
                  </p>
                </div>

                {/* Response */}
                {item.response_text && (
                  <div className="border-t border-slate-100 pt-2.5 mt-2.5">
                    <span className="text-[10px] font-bold text-vyapar-600 uppercase tracking-wider flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      AI Response
                    </span>
                    <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                      {item.response_text}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Footer link */}
      <div className="flex justify-center pb-4">
        <Link
          href="/voice"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 hover:border-vyapar-400 hover:bg-vyapar-50 text-slate-700 hover:text-vyapar-800 rounded-xl text-xs font-semibold shadow-xs transition-colors"
        >
          <Mic className="w-4 h-4" />
          Back to Voice Assistant
        </Link>
      </div>
    </div>
  );
}
