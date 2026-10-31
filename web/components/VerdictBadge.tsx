const STYLES: Record<string, string> = {
  missing: "bg-rose-500/15 text-rose-300 ring-rose-500/30",
  stale: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  partial: "bg-yellow-500/15 text-yellow-200 ring-yellow-500/30",
  satisfied: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const style = STYLES[verdict] ?? "bg-slate-500/15 text-slate-300 ring-slate-500/30";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {verdict}
    </span>
  );
}
