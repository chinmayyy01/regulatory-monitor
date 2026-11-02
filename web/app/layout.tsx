import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RegIntel",
  description: "Know which regulations bind you, what went stale, and what to edit.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
