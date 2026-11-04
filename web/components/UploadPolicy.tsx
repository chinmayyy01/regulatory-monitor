"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

const MAX_BYTES = 10 * 1024 * 1024;

export function UploadPolicy({ tenantId, compact = false }: { tenantId: number; compact?: boolean }) {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function upload(files: FileList | File[] | null) {
    if (!files || files.length === 0 || busy) return;
    setBusy(true);
    setError(null);
    setStatus(null);

    let uploaded = 0;
    const failures: string[] = [];
    const selected = Array.from(files);

    for (const file of selected) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        failures.push(`${file.name}: choose a PDF file.`);
        continue;
      }
      if (file.size > MAX_BYTES) {
        failures.push(`${file.name}: the file is larger than 10 MB.`);
        continue;
      }
      const body = new FormData();
      body.append("tenantId", String(tenantId));
      body.append("file", file);
      try {
        const response = await fetch("/api/upload", { method: "POST", body });
        if (response.ok) {
          uploaded += 1;
        } else {
          const data = await response.json().catch(() => ({}));
          failures.push(`${file.name}: ${data?.detail ?? "The file could not be added."}`);
        }
      } catch {
        failures.push(`${file.name}: couldn’t connect. Check your connection and try again.`);
      }
    }

    setBusy(false);
    if (uploaded) {
      setStatus(`${uploaded} policy PDF${uploaded === 1 ? "" : "s"} added. Refreshing your workspace…`);
      router.refresh();
    }
    if (failures.length) setError(failures.join("\n"));
    if (input.current) input.current.value = "";
  }

  return (
    <div
      className={`workspace-upload ${compact ? "workspace-upload-compact" : ""}`}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        void upload(event.dataTransfer.files);
      }}
    >
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        aria-label="Choose policy PDF files"
        className="sr-only"
        tabIndex={-1}
        onChange={(event) => void upload(event.target.files)}
      />
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="font-medium">{compact ? "Add policy PDFs" : "Upload your policy documents"}</p>
          <p className="mt-1 text-sm leading-5 text-[var(--ws-muted)]">
            PDF only · up to 10 MB per file · text stays on this machine
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => input.current?.click()}
          className="workspace-button workspace-button-secondary min-h-11 shrink-0 px-4 disabled:cursor-wait disabled:opacity-60"
        >
          {busy ? "Adding PDFs…" : "Choose PDF files"}
        </button>
      </div>
      {!compact ? <p className="mt-3 text-sm text-[var(--ws-muted)]">You can also drag PDF files into this area.</p> : null}
      {status ? <p aria-live="polite" role="status" className="mt-3 text-sm text-[var(--ws-positive)]">{status}</p> : null}
      {error ? <p role="alert" className="workspace-error mt-3 whitespace-pre-line text-sm">{error}</p> : null}
    </div>
  );
}
