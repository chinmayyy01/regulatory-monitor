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
      <body className="min-h-screen antialiased">
        <header className="border-b border-slate-800">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <a href="/" className="flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-emerald-500/15 text-sm font-semibold text-emerald-400">
                R
              </span>
              <span className="text-lg font-semibold tracking-tight">RegIntel</span>
            </a>
            <span className="text-xs text-slate-500">
              informational, not legal advice
            </span>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
