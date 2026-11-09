import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import BottomNav from "@/components/BottomNav";

export const metadata: Metadata = {
  title: "VyaparVoice — Your Shop, Ready to Speak",
  description: "Multilingual Voice-First Business Management for Small Indian Shopkeepers powered by Gnani.ai",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
        <AuthProvider>
          <Navbar />
          <div className="flex-1 flex flex-col lg:flex-row pb-16 lg:pb-0">
            <Sidebar />
            <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
              {children}
            </main>
          </div>
          <BottomNav />
        </AuthProvider>
      </body>
    </html>
  );
}
