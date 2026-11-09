"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "@/lib/api";

interface User {
  id: string;
  full_name: string;
  email: string;
  phone?: string;
  preferred_language: string;
}

interface Business {
  id: string;
  business_name: string;
  business_type: string;
  GSTIN?: string;
  currency: string;
  timezone: string;
  address?: string;
}

interface AuthContextType {
  user: User | null;
  business: Business | null;
  token: string | null;
  loading: boolean;
  language: string;
  setLanguage: (lang: string) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string, phone?: string, lang?: string) => Promise<void>;
  logout: () => void;
  refreshBusiness: () => Promise<void>;
  seedDemo: () => Promise<any>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [business, setBusiness] = useState<Business | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguageState] = useState("en");

  const setLanguage = (lang: string) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("vyapar_lang", lang);
    }
  };

  useEffect(() => {
    const savedToken = localStorage.getItem("vyapar_token");
    const savedUser = localStorage.getItem("vyapar_user");
    const savedLang = localStorage.getItem("vyapar_lang");

    if (savedLang) {
      setLanguageState(savedLang);
    }

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      fetchActiveBusiness();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchActiveBusiness = async () => {
    try {
      const b = await api.getCurrentBusiness();
      setBusiness(b);
      if (typeof window !== "undefined" && b?.id) {
        localStorage.setItem("vyapar_business_id", b.id);
      }
    } catch (err) {
      console.error("Failed to fetch active business:", err);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await api.login({ email, password });
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem("vyapar_token", res.access_token);
      localStorage.setItem("vyapar_user", JSON.stringify(res.user));
      if (res.user?.preferred_language) {
        setLanguage(res.user.preferred_language);
      }
      await fetchActiveBusiness();
    } finally {
      setLoading(false);
    }
  };

  const register = async (fullName: string, email: string, password: string, phone?: string, lang = "en") => {
    setLoading(true);
    try {
      await api.register({
        full_name: fullName,
        email,
        password,
        phone,
        preferred_language: lang
      });
      // Auto login
      await login(email, password);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setBusiness(null);
    setToken(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("vyapar_token");
      localStorage.removeItem("vyapar_user");
      localStorage.removeItem("vyapar_business_id");
      window.location.href = "/login";
    }
  };

  const seedDemo = async () => {
    return await api.seedDemoData();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        business,
        token,
        loading,
        language,
        setLanguage,
        login,
        register,
        logout,
        refreshBusiness: fetchActiveBusiness,
        seedDemo
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
