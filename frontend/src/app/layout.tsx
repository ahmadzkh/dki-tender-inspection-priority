import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Prioritas Pemeriksaan Tender DKI Jakarta",
  description: "Sistem prioritas pemeriksaan realisasi tender DKI Jakarta",
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: Readonly<RootLayoutProps>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
