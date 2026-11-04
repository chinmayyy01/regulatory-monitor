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
    setResult(`Starting a check for the next ${count} obligations…`);
    try {
      const response = await fetch("/api/map", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenantId, limit: count }),
      });
      const job = await response.json();
      if (!response.ok) {
        setResult(job?.detail ?? "The check could not be started. Try again.");
        return;
      }

      for (let attempt = 0; attempt < 120; attempt += 1) {
        await sleep(2000);
        const poll = await fetch(`/api/job?tenantId=${tenantId}&jobId=${job.job_id}`);
        if (!poll.ok) continue;
        const status = (await poll.json()) as JobStatus;
        if (status.status === "done") {
          setResult(`Check complete. ${status.mapped} obligations reviewed. ${status.detail}`);
          router.refresh();
          return;
        }
        if (status.status === "failed") {
          setResult(status.detail || "The check did not finish. Try again.");
          return;
        }
        setResult(status.status === "queued" ? "Your check is queued…" : "Checking policy evidence…");
      }
      setResult("This check is still running. You can stay here and refresh in a moment.");
    } catch {
      setResult("We couldn’t reach the assessment service. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={() => void run()}
        disabled={busy}
        aria-describedby={`check-help-${tenantId}`}
        className="workspace-button workspace-button-primary min-h-11 px-4 disabled:cursor-wait disabled:opacity-60"
      >
        {busy ? "Checking policies…" : `Check next ${count} obligations`}
      </button>
      <span id={`check-help-${tenantId}`} className="text-sm text-[var(--ws-muted)]">
        Checks a small batch. You can run it again to continue.
      </span>
      {result ? <p aria-live="polite" role="status" className="w-full text-sm text-[var(--ws-muted)]">{result}</p> : null}
    </div>
  );
}
