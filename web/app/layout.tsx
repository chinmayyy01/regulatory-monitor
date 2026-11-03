import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "RegIntel",
  description: "Know which regulations bind you, what went stale, and what to edit.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${manrope.className} min-h-screen bg-black text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
