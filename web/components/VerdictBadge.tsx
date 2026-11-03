const STYLES: Record<string, string> = {
  satisfied: "bg-emerald-500/10 text-emerald-300 ring-emerald-500/30",
  partial: "bg-amber-500/10 text-amber-300 ring-amber-500/30",
  stale: "bg-white/5 text-[#9B9B9B] ring-[#313131]",
  missing: "bg-rose-500/10 text-rose-300 ring-rose-500/30",
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const style = STYLES[verdict] ?? "bg-white/5 text-[#9B9B9B] ring-[#313131]";
  return (
    <span
      className={`caption-3 inline-flex items-center rounded-full px-3 py-1 ring-1 ring-inset ${style}`}
    >
      {verdict}
    </span>
  );
}
