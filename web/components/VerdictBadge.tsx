const LABELS: Record<string, string> = {
  satisfied: "Appears covered",
  partial: "Partial match",
  missing: "No matching clause",
  stale: "May be out of date",
};

const STYLES: Record<string, string> = {
  satisfied: "workspace-verdict-covered",
  partial: "workspace-verdict-partial",
  stale: "workspace-verdict-stale",
  missing: "workspace-verdict-missing",
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  return (
    <span className={`workspace-verdict ${STYLES[verdict] ?? "workspace-verdict-stale"}`}>
      {LABELS[verdict] ?? verdict}
    </span>
  );
}
