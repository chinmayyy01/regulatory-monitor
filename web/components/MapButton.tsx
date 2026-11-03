"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type JobStatus = { job_id: number; status: string; mapped: number; detail: string };

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function MapButton({ tenantId, count = 10 }: { tenantId: number; count?: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setResult("queued…");
    try {
      const response = await fetch("/api/map", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenantId, limit: count }),
      });
      const job = await response.json();
      if (!response.ok) {
        setResult(job?.detail ?? "mapping failed");
        return;
      }

      for (let attempt = 0; attempt < 120; attempt += 1) {
        await sleep(2000);
        const poll = await fetch(`/api/job?tenantId=${tenantId}&jobId=${job.job_id}`);
        if (!poll.ok) continue;
        const status = (await poll.json()) as JobStatus;
        if (status.status === "done") {
          setResult(`${status.mapped} mapped · ${status.detail}`);
          router.refresh();
          return;
        }
        if (status.status === "failed") {
          setResult(status.detail || "mapping failed");
          return;
        }
        setResult(`${status.status}…`);
      }
      setResult("still running, refresh in a moment");
    } catch {
      setResult("mapping failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-4">
      <button
        type="button"
        onClick={() => void run()}
        disabled={busy}
        className="btn-ghost caption-1 rounded-full px-3 py-2 disabled:opacity-40"
      >
        {busy ? "Checking…" : `Re-check ${count} obligations`}
      </button>
      {result ? <span className="caption-2 muted">{result}</span> : null}
    </div>
  );
}
