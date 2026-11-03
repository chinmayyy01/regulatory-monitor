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
  if (!span) {
    return <>{text.length > 240 ? `${text.slice(0, 240)}…` : text}</>;
  }
  const start = Math.max(0, span.start - 90);
  const end = Math.min(text.length, span.end + 90);
  return (
    <>
      {start > 0 ? "…" : null}
      {text.slice(start, span.start)}
      <mark className="rounded-sm bg-white/15 px-1 text-white">
        {text.slice(span.start, span.end)}
      </mark>
      {text.slice(span.end, end)}
      {end < text.length ? "…" : null}
    </>
  );
}

export function GapCard({ gap, tenantId }: { gap: Gap; tenantId: number }) {
  return (
    <article className="surface rounded-2xl p-6">
      <div className="flex items-start justify-between gap-4">
        <p className="title-2 text-white">
          {gap.action}
          {gap.condition ? <span className="muted"> — {gap.condition}</span> : null}
        </p>
        <VerdictBadge verdict={gap.verdict} />
      </div>

      {gap.reason ? <p className="body-6 muted mt-3">{gap.reason}</p> : null}

      <dl className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="surface-2 rounded-lg p-4">
          <dt className="caption-4 uppercase tracking-wide text-[#6B6B6B]">regulation</dt>
          <dd className="body-6 mt-2 text-[#D4D4D4]">
            {gap.evidence_regulation ? `“${gap.evidence_regulation}”` : gap.action}
          </dd>
        </div>
        <div className="surface-2 rounded-lg p-4">
          <dt className="caption-4 uppercase tracking-wide text-[#6B6B6B]">your policy</dt>
          <dd className="body-6 mt-2 text-[#D4D4D4]">
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

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <Link
          href={`/tenants/${tenantId}/obligations/${gap.obligation_id}`}
          className="app-link caption-1 underline"
        >
          open detail
        </Link>
        {gap.document_id && gap.page ? (
          <a
            href={`/api/pdf?tenantId=${tenantId}&documentId=${gap.document_id}#page=${gap.page}`}
            target="_blank"
            rel="noreferrer"
            className="app-link caption-1 underline"
          >
            source page {gap.page}
          </a>
        ) : null}
        {gap.document_title ? (
          <span className="caption-4 text-[#6B6B6B]">
            {gap.document_title}
            {gap.section_no ? ` · s.${gap.section_no}` : ""}
          </span>
        ) : null}
      </div>
    </article>
  );
}
