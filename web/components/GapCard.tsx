import type { Gap } from "@/lib/api";
import { VerdictBadge } from "./VerdictBadge";

function Excerpt({
  text,
  span,
}: {
  text: string;
  span: { start: number; end: number } | null;
}) {
  if (!span) {
    return <>{text.length > 240 ? `${text.slice(0, 240)}…` : text}</>;
  }
  const start = Math.max(0, span.start - 90);
  const end = Math.min(text.length, span.end + 90);
  return (
    <>
      {start > 0 ? "…" : null}
      {text.slice(start, span.start)}
      <mark className="rounded bg-emerald-500/20 px-0.5 text-emerald-100">
        {text.slice(span.start, span.end)}
      </mark>
      {text.slice(span.end, end)}
      {end < text.length ? "…" : null}
    </>
  );
}

export function GapCard({ gap }: { gap: Gap }) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-medium leading-6 text-slate-100">
          {gap.action}
          {gap.condition ? (
            <span className="text-slate-400"> — {gap.condition}</span>
          ) : null}
        </p>
        <VerdictBadge verdict={gap.verdict} />
      </div>

      {gap.reason ? (
        <p className="mt-3 text-sm leading-6 text-slate-400">{gap.reason}</p>
      ) : null}

      <dl className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-slate-950/60 p-3">
          <dt className="text-[11px] uppercase tracking-wide text-slate-500">
            regulation
          </dt>
          <dd className="mt-1 text-sm leading-6 text-slate-300">
            {gap.evidence_regulation ? (
              `“${gap.evidence_regulation}”`
            ) : (
              <span className="text-slate-400">{gap.action}</span>
            )}
          </dd>
        </div>
        <div className="rounded-lg bg-slate-950/60 p-3">
          <dt className="text-[11px] uppercase tracking-wide text-slate-500">
            your policy
          </dt>
          <dd className="mt-1 text-sm leading-6 text-slate-300">
            {gap.clause_text && gap.evidence_policy ? (
              <Excerpt text={gap.clause_text} span={gap.policy_span} />
            ) : gap.evidence_policy ? (
              `“${gap.evidence_policy}”`
            ) : (
              <span className="text-rose-300/80">no matching clause found</span>
            )}
          </dd>
        </div>
      </dl>

      {gap.document_title ? (
        <p className="mt-3 text-xs text-slate-500">
          {gap.document_title}
          {gap.section_no ? ` · s.${gap.section_no}` : ""}
        </p>
      ) : null}
    </article>
  );
}
