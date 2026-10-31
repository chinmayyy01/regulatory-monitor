"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function MapButton({ tenantId, count = 5 }: { tenantId: number; count?: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setResult(null);
    try {
      const response = await fetch("/api/map", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenantId, limit: count }),
      });
      const data = await response.json();
      if (!response.ok) {
        setResult(data?.detail ?? "mapping failed");
        return;
      }
      setResult(
        `${data.mapped} mapped · ${data.rejected} rejected · ${data.applicable} applicable`,
      );
      router.refresh();
    } catch {
      setResult("mapping failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => void run()}
        disabled={busy}
        className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-200 transition hover:border-slate-600 disabled:opacity-40"
      >
        {busy ? `Checking ${count}…` : `Re-check ${count} obligations`}
      </button>
      {result ? <span className="text-xs text-slate-500">{result}</span> : null}
    </div>
  );
}
