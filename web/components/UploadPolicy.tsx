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
    <div className="surface rounded-2xl p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="title-3 text-white">Add a policy</p>
          <p className="caption-2 muted mt-2">
            PDF, up to 10 MB. Text is extracted and embedded on this machine.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => input.current?.click()}
          className="btn-ghost caption-1 rounded-full px-3 py-2 disabled:opacity-40"
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

      {status ? <p className="caption-2 mt-4 text-emerald-300">{status}</p> : null}
      {error ? (
        <p className="caption-2 mt-4 whitespace-pre-line text-rose-300">{error}</p>
      ) : null}
    </div>
  );
}
