"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { translations } from "@/lib/translations";
import Link from "next/link";
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  RotateCcw,
  Languages,
  ShieldCheck,
  Check,
  X
} from "lucide-react";

interface Interaction {
  id: string;
  sender: "user" | "assistant";
  text: string;
  language?: string;
  intent?: string;
  status?: string;
  audioBase64?: string;
  confirmationToken?: string;
  pendingAction?: {
    action_type: string;
    summary: string;
    params: any;
  };
  timestamp: Date;
}

export default function VoiceAssistantPage() {
  const { user, business, language, setLanguage } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [inputText, setInputText] = useState("");
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [activeConfirmation, setActiveConfirmation] = useState<any>(null);
  const [gnaniStatus, setGnaniStatus] = useState<any>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const t = translations[language] || translations.en;

  useEffect(() => {
    checkGnaniConnectivity();
  }, []);

  const checkGnaniConnectivity = async () => {
    try {
      const status = await api.getGnaniStatus();
      setGnaniStatus(status);
    } catch (err) {
      console.error(err);
    }
  };

  const quickPrompts = [
    { lang: "en", text: "How much did I sell today?", label: "Today's Sales" },
    { lang: "en", text: "Add 10 packets of Nandini Milk", label: "Add 10 Milk (Stock)" },
    { lang: "en", text: "Sell 2 kg Sona Masoori Rice for 120", label: "Sell Rice (Bill)" },
    { lang: "kn", text: "ಇವತ್ತು ಎಷ್ಟು ಸೇಲ್ ಆಗಿದೆ?", label: "ಇವತ್ತಿನ ಸೇಲ್ಸ್ (ಕನ್ನಡ)" },
    { lang: "kn", text: "10 ಪ್ಯಾಕೆಟ್ ಹಾಲು ಸೇರಿಸಿ", label: "ಹಾಲು ಸ್ಟಾಕ್ (ಕನ್ನಡ)" },
    { lang: "ml", text: "ഇന്ന് എത്ര രൂപയുടെ വിൽപ്പനയായി?", label: "വിൽപ്പന എത്ര? (മലയാളം)" },
    { lang: "hi", text: "आज कितनी बिक्री हुई?", label: "आज की बिक्री (हिन्दी)" },
    { lang: "hi", text: "रमेश ने 200 रुपये दिए", label: "रमेश भुगतान (हिन्दी)" },
    { lang: "ta", text: "இன்று எவ்வளவு விற்றோம்?", label: "இன்றைய விற்பனை (தமிழ்)" },
    { lang: "ta", text: "இன்றைய லாபம் எவ்வளவு?", label: "இன்றைய லாபம் (தமிழ்)" },
    { lang: "ta", text: "இன்று எவ்வளவு விற்றோம்?", label: "இன்றைய விற்பனை (தமிழ்)" },
  ];

  useEffect(() => {
    // Initial welcome message
    const welcome = language === "kn"
      ? "ನಮಸ್ಕಾರ! ವ್ಯಾಪಾರವಾಯ್ಸ್ ಗೆ ಸುಸ್ವಾಗತ. ನೀವು ಮಾರಾಟ, ದಾಸ್ತಾನು ಅಥವಾ ಸಾಲದ ಮಾಹಿತಿಯನ್ನು ಧ್ವನಿಯ ಮೂಲಕ ಕೇಳಬಹುದು."
      : language === "ml"
      ? "നമസ്കാരം! വ്യാപാരവോയിസിലേക്ക് സ്വാഗതം. വിൽപ്പനയോ സ്റ്റോക്കോ കടമോ ശബ്ദത്തിലൂടെ നിയന്ത്രിക്കാം."
      : language === "hi"
      ? "नमस्ते! व्यापारवॉयस में आपका स्वागत है। आप बोलकर बिक्री दर्ज कर सकते हैं या स्टॉक जांच सकते हैं।"
      : language === "ta"
      ? "வணக்கம்! வியாபார வாய்சில் உங்களை வரவேற்கிறோம். குரலில் பேசி விற்பனை, சரக்கு அல்லது கடனை நிர்வகிக்கலாம்."
      : "Welcome to VyaparVoice! Speak or type to record sales, check inventory, or update customer credit.";

    setInteractions([
      {
        id: "welcome-1",
        sender: "assistant",
        text: welcome,
        language,
        timestamp: new Date()
      }
    ]);
  }, [language]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [interactions, processing]);

  // Audio recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Select best supported MIME type
      let mimeType = "audio/webm";
      if (typeof MediaRecorder !== "undefined") {
        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) {
          mimeType = "audio/ogg;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
          mimeType = "audio/mp4";
        } else if (MediaRecorder.isTypeSupported("audio/wav")) {
          mimeType = "audio/wav";
        }
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        if (audioBlob.size < 100) {
          setInteractions((prev) => [
            ...prev,
            {
              id: `err-${Date.now()}`,
              sender: "assistant",
              text: "No audio was captured. Please check your microphone and try speaking again.",
              timestamp: new Date()
            }
          ]);
          return;
        }
        await handleAudioUpload(audioBlob);
      };

      // Stream chunks every 250ms
      mediaRecorder.start(250);
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied or error:", err);
      alert("Microphone access is unavailable. Please check your browser permissions or use the text box.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAudioUpload = async (blob: Blob) => {
    setProcessing(true);
    try {
      const formData = new FormData();
      const extension = blob.type.includes("wav") ? "wav" : blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "m4a" : "webm";
      formData.append("file", blob, `voice_input.${extension}`);

      // Map language for Gnani Prisma STT
      const sttLang = language === "auto" ? "indic-auto" : language === "en" ? "en-IN" : `${language}-IN`;
      formData.append("language", sttLang);

      // Stage 1: Speech-to-Text Transcription
      const transcribeRes = await api.transcribeAudio(formData);
      const text = transcribeRes.transcription?.trim();
      const detectedLang = transcribeRes.detected_language || sttLang;

      if (text) {
        // Stage 2: Intent Understanding & Business Command Processing
        await executeCommand(text, detectedLang);
      } else {
        // Fallback message if audio is silent
        setInteractions((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            sender: "assistant",
            text: "Could not detect clear speech. Please speak closer to the microphone or type below.",
            timestamp: new Date()
          }
        ]);
      }
    } catch (err: any) {
      console.error("Transcription error:", err);
      const errorMsg = err?.message?.includes("401") || err?.message?.includes("key")
        ? "Voice service is currently reconnecting. You can speak again or type your command below."
        : (err?.message || "Could not process audio. Please try speaking again or type your command below.");

      setInteractions((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: errorMsg,
          timestamp: new Date()
        }
      ]);
    } finally {
      setProcessing(false);
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || processing) return;
    const text = inputText.trim();
    setInputText("");
    await executeCommand(text, language);
  };

  const executeCommand = async (text: string, lang = "auto") => {
    setProcessing(true);

    // Append user interaction
    const userMsg: Interaction = {
      id: `u-${Date.now()}`,
      sender: "user",
      text,
      language: lang,
      timestamp: new Date()
    };
    setInteractions((prev) => [...prev, userMsg]);

    try {
      const res = await api.processVoiceCommand({
        transcription: text,
        language: lang
      });

      const assistantMsg: Interaction = {
        id: `a-${Date.now()}`,
        sender: "assistant",
        text: res.response_text,
        language: res.detected_language,
        intent: res.parsed_intent?.intent,
        status: res.execution_status,
        audioBase64: res.audio_base64,
        confirmationToken: res.confirmation_token,
        pendingAction: res.pending_action,
        timestamp: new Date()
      };

      setInteractions((prev) => [...prev, assistantMsg]);

      if (res.confirmation_token && res.pending_action) {
        setActiveConfirmation({
          token: res.confirmation_token,
          action: res.pending_action
        });
      }

      // Auto-play synthesized voice if available
      if (res.audio_base64) {
        playAudio(res.audio_base64);
      }
    } catch (err: any) {
      console.error("Execution error:", err);
      setInteractions((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: err?.message || "An error occurred while processing your voice command.",
          timestamp: new Date()
        }
      ]);
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirmAction = async (confirmed: boolean) => {
    if (!activeConfirmation?.token) return;
    setProcessing(true);
    const token = activeConfirmation.token;
    setActiveConfirmation(null);

    try {
      const res = await api.confirmVoiceAction({
        confirmation_token: token,
        confirmed
      });

      const confMsg: Interaction = {
        id: `c-${Date.now()}`,
        sender: "assistant",
        text: res.response_text,
        language: res.detected_language,
        status: res.execution_status,
        audioBase64: res.audio_base64,
        timestamp: new Date()
      };

      setInteractions((prev) => [...prev, confMsg]);

      if (res.audio_base64) {
        playAudio(res.audio_base64);
      }
    } catch (err: any) {
      console.error("Confirmation error:", err);
    } finally {
      setProcessing(false);
    }
  };

  const playAudio = (b64: string) => {
    try {
      const audio = new Audio(`data:audio/wav;base64,${b64}`);
      audio.play();
    } catch (e) {
      console.error("Playback failed:", e);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Info Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Multilingual Voice Assistant
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 mt-1">
            Shop Voice Assistant
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300 text-[11px] font-bold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Voice Ready
            </span>
            <span className="text-xs text-slate-500">
              Speak naturally in Kannada, Malayalam, Hindi, or English
            </span>
          </div>
        </div>

        {/* Language selector badge */}
        <div className="flex items-center gap-2 self-start sm:self-center bg-slate-100 p-1.5 rounded-xl border border-slate-200 text-xs">
          <Languages className="w-4 h-4 text-slate-600 ml-1" />
          <button
            onClick={() => setLanguage("auto")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
              language === "auto" ? "bg-white text-vyapar-700 shadow-xs" : "text-slate-600"
            }`}
          >
            Auto
          </button>
          <button
            onClick={() => setLanguage("kn")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
              language === "kn" ? "bg-white text-vyapar-700 shadow-xs" : "text-slate-600"
            }`}
          >
            ಕನ್ನಡ
          </button>
          <button
            onClick={() => setLanguage("ml")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
              language === "ml" ? "bg-white text-vyapar-700 shadow-xs" : "text-slate-600"
            }`}
          >
            മലയാളം
          </button>
          <button
            onClick={() => setLanguage("hi")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
              language === "hi" ? "bg-white text-vyapar-700 shadow-xs" : "text-slate-600"
            }`}
          >
            हिन्दी
          </button>
          <button
            onClick={() => setLanguage("en")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
              language === "en" ? "bg-white text-vyapar-700 shadow-xs" : "text-slate-600"
            }`}
          >
            English
          </button>
          <button
            onClick={() => setLanguage("ta")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
              language === "ta" ? "bg-white text-vyapar-700 shadow-xs" : "text-slate-600"
            }`}
          >
            தமிழ்
          </button>
        </div>
      </div>

      {/* Quick Action Suggestion Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <span className="text-xs font-semibold text-slate-400 shrink-0">Try asking:</span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => executeCommand(p.text, p.lang)}
            className="shrink-0 px-3 py-1.5 bg-white border border-slate-200 hover:border-vyapar-400 hover:bg-vyapar-50 text-slate-700 hover:text-vyapar-800 rounded-xl text-xs font-medium shadow-xs transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Main Conversation Canvas */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm min-h-[420px] max-h-[560px] flex flex-col">
        {/* Messages List */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {interactions.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] p-4 rounded-2xl shadow-xs ${
                  msg.sender === "user"
                    ? "bg-vyapar-600 text-white rounded-br-xs"
                    : "bg-slate-50 border border-slate-200 text-slate-900 rounded-bl-xs"
                }`}
              >
                {/* Assistant header badges */}
                {msg.sender === "assistant" && (
                  <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-200/60 text-[10px] font-semibold text-slate-500">
                    <span className="flex items-center gap-1 text-vyapar-700">
                      <Sparkles className="w-3 h-3" />
                      VyaparVoice AI
                    </span>
                    {msg.intent && (
                      <span className="bg-slate-200 px-1.5 py-0.5 rounded text-slate-700">
                        {msg.intent}
                      </span>
                    )}
                    {msg.audioBase64 && (
                      <button
                        onClick={() => playAudio(msg.audioBase64!)}
                        title="Replay Voice"
                        className="ml-auto text-vyapar-600 hover:text-vyapar-800 flex items-center gap-1"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>Replay</span>
                      </button>
                    )}
                  </div>
                )}

                <p className="text-sm font-medium leading-relaxed whitespace-pre-line">
                  {msg.text}
                </p>

                {/* Inline Confirmation Card */}
                {msg.confirmationToken && msg.pendingAction && activeConfirmation?.token === msg.confirmationToken && (
                  <div className="mt-4 p-3.5 bg-white border border-amber-300 rounded-xl shadow-xs">
                    <div className="flex items-center gap-2 text-amber-800 text-xs font-bold mb-1.5">
                      <ShieldCheck className="w-4 h-4 text-amber-600" />
                      Confirmation Required for Verified DB Action
                    </div>
                    <p className="text-xs text-slate-700 mb-3 font-semibold">
                      {msg.pendingAction.summary}
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleConfirmAction(true)}
                        className="flex-1 py-2 px-3 bg-vyapar-600 hover:bg-vyapar-700 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 shadow-xs transition-colors"
                      >
                        <Check className="w-4 h-4" />
                        {t.confirm}
                      </button>
                      <button
                        onClick={() => handleConfirmAction(false)}
                        className="py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition-colors"
                      >
                        <X className="w-4 h-4" />
                        {t.cancel}
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 px-1">
                {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          ))}

          {/* Recording & processing states */}
          {isRecording && (
            <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-semibold animate-pulse">
              <span className="w-3 h-3 rounded-full bg-emerald-600 animate-ping"></span>
              <span>{t.listening} Speak your business command now...</span>
              <div className="flex items-center gap-1 ml-auto">
                <span className="w-1.5 h-4 bg-emerald-600 rounded soundwave-bar"></span>
                <span className="w-1.5 h-6 bg-emerald-600 rounded soundwave-bar" style={{ animationDelay: "0.2s" }}></span>
                <span className="w-1.5 h-3 bg-emerald-600 rounded soundwave-bar" style={{ animationDelay: "0.4s" }}></span>
              </div>
            </div>
          )}

          {processing && !isRecording && (
            <div className="flex items-center gap-2 text-slate-500 text-xs py-2 px-3">
              <span className="w-2 h-2 rounded-full bg-vyapar-500 animate-ping"></span>
              <span>Processing your voice command...</span>
            </div>
          )}
          <div ref={scrollRef} />
        </div>

        {/* Voice Control & Input Dock */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 rounded-b-2xl flex flex-col items-center gap-4">
          {/* Main Giant Microphone Button */}
          <div className="flex flex-col items-center">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={processing}
              className={`w-20 h-20 rounded-full flex items-center justify-center text-white shadow-xl transition-transform active:scale-95 ${
                isRecording
                  ? "bg-red-600 recording-pulse"
                  : "bg-vyapar-600 hover:bg-vyapar-700 shadow-vyapar-300"
              }`}
              title={isRecording ? "Click to Stop Recording" : "Click to Speak"}
            >
              {isRecording ? (
                <MicOff className="w-9 h-9 animate-bounce" />
              ) : (
                <Mic className="w-9 h-9" />
              )}
            </button>
            <p className="text-xs font-semibold text-slate-600 mt-2">
              {isRecording ? "Tap to Finish & Submit" : "Tap Microphone to Speak"}
            </p>
          </div>

          {/* Text input fallback */}
          <form onSubmit={handleTextSubmit} className="w-full flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Or type a command: 'How much did I sell today?' or 'Add 10 packets milk'"
              className="flex-1 px-4 py-2.5 text-sm bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-vyapar-500 shadow-xs"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || processing}
              className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs transition-colors"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      {/* View History Link */}
      <div className="flex justify-center">
        <Link
          href="/voice/history"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 hover:border-vyapar-400 hover:bg-vyapar-50 text-slate-600 hover:text-vyapar-800 rounded-xl text-xs font-semibold shadow-xs transition-colors"
        >
          <Clock className="w-4 h-4" />
          View Voice History
        </Link>
      </div>
    </div>
  );
}





