import type { Metadata } from "next";
import { Inter } from "next/font/google";

import "./globals.css";

import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});



export const metadata: Metadata = {
  title: "Prioritas Pemeriksaan Tender DKI Jakarta",
  description: "Sistem prioritas pemeriksaan realisasi tender DKI Jakarta",
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: Readonly<RootLayoutProps>) {
  return (
    <html lang="id" className={`${inter.variable} antialiased`} suppressHydrationWarning>
      <body className="flex min-h-screen flex-col font-sans">
        <Header />
        <main className="flex-1 flex flex-col">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
