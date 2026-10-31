"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

export function UploadPolicy({ tenantId }: { tenantId: number }) {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function upload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setBusy(true);
    setError(null);
    setStatus(null);

    let uploaded = 0;
    const failures: string[] = [];

    for (const file of Array.from(files)) {
      const body = new FormData();
      body.append("tenantId", String(tenantId));
      body.append("file", file);
      const response = await fetch("/api/upload", { method: "POST", body });
      if (response.ok) {
        uploaded += 1;
      } else {
        const data = await response.json().catch(() => ({}));
        failures.push(`${file.name}: ${data?.detail ?? "upload failed"}`);
      }
    }

    setBusy(false);
    if (uploaded) {
      setStatus(`${uploaded} document${uploaded === 1 ? "" : "s"} added and embedded.`);
      router.refresh();
    }
    if (failures.length) setError(failures.join("\n"));
    if (input.current) input.current.value = "";
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-200">Add a policy</p>
          <p className="mt-1 text-xs text-slate-500">
            PDF, up to 10 MB. Text is extracted and embedded on this machine.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => input.current?.click()}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-200 transition hover:border-slate-600 disabled:opacity-40"
        >
          {busy ? "Uploading…" : "Choose PDF"}
        </button>
      </div>

      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        hidden
        onChange={(event) => void upload(event.target.files)}
      />

      {status ? <p className="mt-3 text-xs text-emerald-300">{status}</p> : null}
      {error ? (
        <p className="mt-3 whitespace-pre-line text-xs text-rose-300">{error}</p>
      ) : null}
    </div>
  );
}
