"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function NewWorkspace() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [entityType, setEntityType] = useState("nbfc");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const response = await fetch("/api/workspace", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, entityType }),
    });
    const data = await response.json().catch(() => ({}));
    setBusy(false);
    if (!response.ok) {
      setError(data?.detail ?? data?.error ?? "could not create workspace");
      return;
    }
    setOpen(false);
    setName("");
    router.refresh();
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-200 transition hover:border-slate-600"
      >
        New workspace
      </button>
    );
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4"
    >
      <label className="block">
        <span className="text-xs uppercase tracking-wide text-slate-500">name</span>
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          minLength={2}
          className="mt-1 w-56 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-500/60"
        />
      </label>
      <label className="block">
        <span className="text-xs uppercase tracking-wide text-slate-500">entity type</span>
        <select
          value={entityType}
          onChange={(event) => setEntityType(event.target.value)}
          className="mt-1 w-48 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-500/60"
        >
          <option value="nbfc">NBFC</option>
          <option value="commercial_bank">commercial bank</option>
          <option value="payments_bank">payments bank</option>
          <option value="small_finance_bank">small finance bank</option>
          <option value="cooperative_bank">cooperative bank</option>
          <option value="housing_finance">housing finance</option>
          <option value="mutual_fund">mutual fund</option>
          <option value="stock_broker">stock broker</option>
        </select>
      </label>
      <button
        type="submit"
        disabled={busy}
        className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 disabled:opacity-40"
      >
        {busy ? "Creating…" : "Create"}
      </button>
      <button
        type="button"
        onClick={() => setOpen(false)}
        className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300"
      >
        Cancel
      </button>
      {error ? <p className="w-full text-xs text-rose-300">{error}</p> : null}
    </form>
  );
}
