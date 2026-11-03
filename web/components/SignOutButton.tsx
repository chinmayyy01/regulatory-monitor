"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function SignOutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  return (
    <button
      type="button"
      disabled={loading}
      onClick={async () => {
        setLoading(true);
        await fetch("/api/logout", { method: "POST" });
        router.replace("/login");
        router.refresh();
      }}
      className="btn-ghost caption-1 rounded-full px-3 py-1.5 disabled:opacity-40"
    >
      {loading ? "Signing out…" : "Sign out"}
    </button>
  );
}
