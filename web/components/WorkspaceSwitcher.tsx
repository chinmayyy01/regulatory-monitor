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

  if (memberships.length <= 1) return null;

  async function switchTo(tenantId: number) {
    setBusy(tenantId);
    await fetch("/api/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tenantId }),
    });
    setBusy(null);
    router.refresh();
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs uppercase tracking-wide text-slate-500">workspaces</span>
      {memberships.map((membership) => (
        <button
          key={membership.tenant_id}
          type="button"
          disabled={busy !== null}
          onClick={() => switchTo(membership.tenant_id)}
          className={`rounded-full border px-3 py-1 text-xs transition disabled:opacity-40 ${
            membership.tenant_id === activeId
              ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-200"
              : "border-slate-800 text-slate-300 hover:border-slate-700"
          }`}
        >
          {membership.name}
        </button>
      ))}
    </div>
  );
}
