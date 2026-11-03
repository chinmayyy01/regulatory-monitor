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
        className="btn-ghost caption-1 rounded-full px-3 py-1.5"
      >
        New workspace
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="surface flex flex-wrap items-end gap-3 rounded-2xl p-4">
      <label className="block">
        <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">name</span>
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          minLength={2}
          className="input mt-2 w-56 rounded-lg px-3 py-2 text-sm"
        />
      </label>
      <label className="block">
        <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">entity type</span>
        <select
          value={entityType}
          onChange={(event) => setEntityType(event.target.value)}
          className="input mt-2 w-48 rounded-lg px-3 py-2 text-sm"
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
      <button type="submit" disabled={busy} className="btn-primary caption-1 rounded-full px-4 py-2 disabled:opacity-40">
        {busy ? "Creating…" : "Create"}
      </button>
      <button type="button" onClick={() => setOpen(false)} className="btn-ghost caption-1 rounded-full px-3 py-2">
        Cancel
      </button>
      {error ? <p className="caption-2 w-full text-rose-300">{error}</p> : null}
    </form>
  );
}
