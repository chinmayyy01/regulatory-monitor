"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@regintel.dev");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(data?.detail ?? "sign in failed");
        return;
      }
      router.replace("/");
      router.refresh();
    } catch {
      setError("sign in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="max-w-sm space-y-4">
      <label className="block">
        <span className="text-xs uppercase tracking-wide text-slate-500">email</span>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="username"
          className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-500/60"
        />
      </label>

      <label className="block">
        <span className="text-xs uppercase tracking-wide text-slate-500">password</span>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-500/60"
        />
      </label>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-40"
      >
        {loading ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
