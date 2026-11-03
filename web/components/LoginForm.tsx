"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LoginForm({ googleEnabled = false }: { googleEnabled?: boolean }) {
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
      router.replace("/app");
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
        <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">email</span>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="username"
          className="input mt-2 w-full rounded-lg px-3 py-2 text-sm"
        />
      </label>

      <label className="block">
        <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">password</span>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          className="input mt-2 w-full rounded-lg px-3 py-2 text-sm"
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
        className="btn-primary button-md w-full rounded-full px-4 py-2 disabled:opacity-40"
      >
        {loading ? "Signing in…" : "Sign in"}
      </button>

      {googleEnabled ? (
        <>
          <div className="muted caption-2 flex items-center gap-3">
            <span className="h-px flex-1 bg-[#272727]" />
            or
            <span className="h-px flex-1 bg-[#272727]" />
          </div>
          <a
            href="/api/auth/google/start"
            className="btn-ghost caption-1 block w-full rounded-full px-4 py-2 text-center"
          >
            Continue with Google
          </a>
        </>
      ) : null}
    </form>
  );
}
