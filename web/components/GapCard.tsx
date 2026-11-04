import Link from "next/link";
import type { Gap } from "@/lib/api";
import { VerdictBadge } from "./VerdictBadge";

function Excerpt({
  text,
  span,
}: {
  text: string;
  span: { start: number; end: number } | null;
}) {
  if (!span || span.start < 0 || span.end > text.length) {
    return <>{text.length > 320 ? `${text.slice(0, 320)}…` : text}</>;
  }
  const start = Math.max(0, span.start - 100);
  const end = Math.min(text.length, span.end + 100);
  return (
    <>
      {start > 0 ? "…" : null}
      {text.slice(start, span.start)}
      <mark className="workspace-evidence-highlight">{text.slice(span.start, span.end)}</mark>
      {text.slice(span.end, end)}
      {end < text.length ? "…" : null}
    </>
  );
}

export function GapCard({ gap, tenantId }: { gap: Gap; tenantId: number }) {
  return (
    <article className="workspace-panel p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="min-w-0 flex-1 text-base font-semibold leading-6">
          {gap.action}
          {gap.condition ? <span className="font-normal text-[var(--ws-muted)]"> — {gap.condition}</span> : null}
        </h3>
        <VerdictBadge verdict={gap.verdict} />
      </div>

      {gap.reason ? <p className="mt-2 max-w-4xl text-sm leading-5 text-[var(--ws-muted)]">{gap.reason}</p> : null}

      <dl className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="workspace-evidence-block">
          <dt>Regulatory requirement</dt>
          <dd>{gap.evidence_regulation ? `“${gap.evidence_regulation}”` : gap.action}</dd>
        </div>
        <div className="workspace-evidence-block">
          <dt>Evidence in your policy</dt>
          <dd>
            {gap.clause_text && gap.evidence_policy ? (
              <Excerpt text={gap.clause_text} span={gap.policy_span} />
            ) : gap.evidence_policy ? (
              `“${gap.evidence_policy}”`
            ) : (
              <span className="text-[var(--ws-muted)]">No matching policy text was found in this assessment.</span>
            )}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-[var(--ws-border)] pt-3">
        <Link href={`/tenants/${tenantId}/obligations/${gap.obligation_id}`} className="workspace-text-link min-h-11 inline-flex items-center">
          Review both sources <span className="sr-only"> for: {gap.action}</span>
        </Link>
        {gap.document_id && gap.page ? (
          <a
            href={`/api/pdf?tenantId=${tenantId}&documentId=${gap.document_id}#page=${gap.page}`}
            target="_blank"
            rel="noreferrer"
            className="workspace-text-link min-h-11 inline-flex items-center"
          >
            Open policy PDF, page {gap.page}
          </a>
        ) : null}
        {gap.document_title ? <span className="text-sm text-[var(--ws-muted)]">{gap.document_title}{gap.section_no ? ` · Section ${gap.section_no}` : ""}</span> : null}
      </div>
    </article>
  );
}
