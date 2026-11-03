"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const ENTITIES = [
  ["nbfc", "NBFC"],
  ["commercial_bank", "commercial bank"],
  ["payments_bank", "payments bank"],
  ["small_finance_bank", "small finance bank"],
  ["cooperative_bank", "cooperative bank"],
  ["housing_finance", "housing finance"],
  ["mutual_fund", "mutual fund"],
  ["stock_broker", "stock broker"],
];

export function SignupForm({ googleEnabled = false }: { googleEnabled?: boolean }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [workspace, setWorkspace] = useState("");
  const [entityType, setEntityType] = useState("nbfc");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const passwordTooShort = password.length > 0 && password.length < 12;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, workspace, entityType }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(data?.detail ?? data?.error ?? "could not create the account");
        return;
      }
      router.replace("/app");
      router.refresh();
    } catch {
      setError("could not create the account");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <label className="block">
        <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">work email</span>
        <input
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          className="input mt-2 w-full rounded-lg px-3 py-2 text-sm"
        />
      </label>

      <label className="block">
        <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">password</span>
        <input
          type="password"
          required
          minLength={12}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
          className="input mt-2 w-full rounded-lg px-3 py-2 text-sm"
        />
        <span className={`caption-2 mt-2 block ${passwordTooShort ? "text-rose-300" : "muted"}`}>
          at least 12 characters
        </span>
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">workspace</span>
          <input
            required
            minLength={2}
            value={workspace}
            onChange={(event) => setWorkspace(event.target.value)}
            placeholder="acme lending"
            className="input mt-2 w-full rounded-lg px-3 py-2 text-sm"
          />
        </label>

        <label className="block">
          <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">entity type</span>
          <select
            value={entityType}
            onChange={(event) => setEntityType(event.target.value)}
            className="input mt-2 w-full rounded-lg px-3 py-2 text-sm"
          >
            {ENTITIES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={busy || passwordTooShort}
        className="btn-primary button-md w-full rounded-full px-4 py-2 disabled:opacity-40"
      >
        {busy ? "Creating workspace…" : "Create workspace"}
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
