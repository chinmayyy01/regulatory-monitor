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
      <span className="caption-4 uppercase tracking-wide text-[#6B6B6B]">workspaces</span>
      {memberships.map((membership) => (
        <button
          key={membership.tenant_id}
          type="button"
          disabled={busy !== null}
          onClick={() => switchTo(membership.tenant_id)}
          className={`caption-1 rounded-full border px-3 py-1 transition disabled:opacity-40 ${
            membership.tenant_id === activeId
              ? "border-white/40 bg-white/10 text-white"
              : "border-[#313131] text-[#9B9B9B] hover:border-[#4A4A4A]"
          }`}
        >
          {membership.name}
        </button>
      ))}
    </div>
  );
}
