"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Membership = { tenant_id: number; name: string; role: string };

export function WorkspaceSwitcher({
  memberships,
  activeId,
}: {
  memberships: Membership[];
  activeId: number;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (memberships.length <= 1) return null;

  async function switchTo(tenantId: number) {
    setBusy(tenantId);
    setError(null);
    try {
      const response = await fetch("/api/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenantId }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(data?.error ?? "We couldn’t switch workspaces. Please try again.");
        return;
      }
      router.refresh();
    } catch {
      setError("We couldn’t connect. Check your connection and try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="workspace-switcher">
      <span className="text-sm text-[var(--ws-muted)]">Switch workspace</span>
      <div className="flex flex-wrap gap-2">
        {memberships.map((membership) => (
          <button
            key={membership.tenant_id}
            type="button"
            disabled={busy !== null}
            aria-pressed={membership.tenant_id === activeId}
            onClick={() => void switchTo(membership.tenant_id)}
            className={`workspace-switch-button min-h-11 px-3 ${membership.tenant_id === activeId ? "is-active" : ""}`}
          >
            {membership.name}
          </button>
        ))}
      </div>
      {error ? <p role="alert" className="workspace-error w-full text-sm">{error}</p> : null}
    </div>
  );
}
