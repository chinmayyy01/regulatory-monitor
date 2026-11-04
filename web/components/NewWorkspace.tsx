"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const ENTITY_TYPES = [
  ["nbfc", "Non-bank finance company (NBFC)"],
  ["commercial_bank", "Commercial bank"],
  ["payments_bank", "Payments bank"],
  ["small_finance_bank", "Small finance bank"],
  ["cooperative_bank", "Co-operative bank"],
  ["housing_finance", "Housing finance company"],
  ["mutual_fund", "Mutual fund"],
  ["stock_broker", "Stock broker"],
];

export function NewWorkspace() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [entityType, setEntityType] = useState("nbfc");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/workspace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), entityType }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(data?.detail ?? data?.error ?? "We couldn’t create the workspace. Please try again.");
        return;
      }
      setOpen(false);
      setName("");
      router.refresh();
    } catch {
      setError("We couldn’t connect. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="workspace-button workspace-button-primary min-h-11 px-5"
      >
        Create workspace
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="workspace-panel w-full max-w-3xl p-5 sm:p-6" aria-labelledby="new-workspace-title">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="new-workspace-title" className="text-lg font-semibold">Create a workspace</h2>
          <p className="mt-1 text-sm leading-5 text-[var(--ws-muted)]">Use one workspace for each regulated entity.</p>
        </div>
        <button type="button" onClick={() => setOpen(false)} className="workspace-button workspace-button-secondary min-h-11 px-4">
          Cancel
        </button>
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <label className="workspace-field">
          <span>Organization name</span>
          <input
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
            minLength={2}
            maxLength={120}
            autoComplete="organization"
            className="workspace-input"
            aria-describedby="workspace-name-help"
          />
          <span id="workspace-name-help" className="workspace-field-help">For example, the company name your team uses.</span>
        </label>
        <label className="workspace-field">
          <span>Regulated entity type</span>
          <select value={entityType} onChange={(event) => setEntityType(event.target.value)} className="workspace-input">
            {ENTITY_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <span className="workspace-field-help">This helps determine which obligations may apply.</span>
        </label>
      </div>
      {error ? <p role="alert" className="workspace-error mt-4">{error}</p> : null}
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button type="submit" disabled={busy || name.trim().length < 2} className="workspace-button workspace-button-primary min-h-11 px-5 disabled:cursor-not-allowed disabled:opacity-50">
          {busy ? "Creating workspace…" : "Create workspace"}
        </button>
      </div>
    </form>
  );
}
