import Link from "next/link";
import { notFound } from "next/navigation";
import { VerdictBadge } from "@/components/VerdictBadge";
import { getObligationDetail, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

function Highlight({
  text,
  span,
}: {
  text: string;
  span: { start: number; end: number } | null;
}) {
  if (!span || span.start < 0 || span.end > text.length) return <>{text}</>;
  return (
    <>
      {text.slice(0, span.start)}
      <mark className="rounded-sm bg-white/15 px-1 text-white">
        {text.slice(span.start, span.end)}
      </mark>
      {text.slice(span.end)}
    </>
  );
}

export default async function ObligationPage({
  params,
}: {
  params: Promise<{ id: string; obligationId: string }>;
}) {
  const { id, obligationId } = await params;
  const tenantId = Number(id);
  const detailId = Number(obligationId);
  if (!Number.isFinite(tenantId) || !Number.isFinite(detailId)) notFound();

  const token = await requireToken();
  const tenants = await listTenants(token);
  const tenant = tenants.find((item) => item.id === tenantId);
  if (!tenant) notFound();

  const detail = await getObligationDetail(tenantId, detailId, token);

  return (
    <div className="workspace-page space-y-7">
      <div>
        <Link href={`/tenants/${tenantId}`} className="workspace-text-link min-h-11 inline-flex items-center">
          ← Back to {tenant.name}
        </Link>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm text-[var(--ws-muted)]">
              Requirement: {detail.modality.replaceAll("_", " ")}{detail.condition ? ` · ${detail.condition}` : ""}
            </p>
            <h1 className="mt-2 max-w-4xl text-2xl font-semibold leading-8 tracking-tight">{detail.action}</h1>
          </div>
          {detail.verdict ? <VerdictBadge verdict={detail.verdict} /> : null}
        </div>
        {detail.scope_entities.length ? (
          <p className="mt-3 text-sm text-[var(--ws-muted)]">Applies to: {detail.scope_entities.join(", ")}</p>
        ) : null}
        {detail.reason ? <p className="mt-4 max-w-4xl text-base leading-6 text-[var(--ws-muted)]">Why this result: {detail.reason}</p> : null}
      </div>

      <div className={`workspace-source-grid ${detail.policy_text ? "" : "workspace-source-grid-missing"}`}>
        <section className="space-y-3" aria-labelledby="regulation-source-title">
          <div>
            <h2 id="regulation-source-title" className="text-lg font-semibold">Regulatory source</h2>
            <p className="mt-1 text-sm text-[var(--ws-muted)]">The text this obligation was taken from.</p>
          </div>
          <div className="workspace-panel p-4 sm:p-5">
            <p className="text-sm font-medium">{detail.regulation_title}</p>
            <p className="mt-1 text-sm text-[var(--ws-muted)]">
              {detail.regulation_section ? `Section ${detail.regulation_section}` : "Section not identified"}
              {detail.regulation_page ? ` · Page ${detail.regulation_page}` : ""}
              {detail.valid_from ? ` · Effective ${detail.valid_from}` : ""}
            </p>
            <blockquote className="mt-4 whitespace-pre-line text-sm leading-6 text-[var(--ws-text-secondary)]">{detail.regulation_text}</blockquote>
          </div>
        </section>

        <section className="space-y-3" aria-labelledby="policy-source-title">
          <div>
            <h2 id="policy-source-title" className="text-lg font-semibold">Your policy evidence</h2>
            <p className="mt-1 text-sm text-[var(--ws-muted)]">The closest text found in this organization’s policies.</p>
          </div>
          {detail.policy_text ? (
            <div className="workspace-panel p-4 sm:p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">{detail.policy_title}</p>
                  <p className="mt-1 text-sm text-[var(--ws-muted)]">
                    {detail.policy_section ? `Section ${detail.policy_section}` : "Section not identified"}
                    {detail.policy_page ? ` · Page ${detail.policy_page}` : ""}
                  </p>
                </div>
                {detail.policy_document_id && detail.policy_page ? (
                  <a
                    href={`/api/pdf?tenantId=${tenantId}&documentId=${detail.policy_document_id}#page=${detail.policy_page}`}
                    target="_blank"
                    rel="noreferrer"
                    className="workspace-text-link min-h-11 inline-flex items-center"
                  >
                    Open PDF, page {detail.policy_page}
                  </a>
                ) : null}
              </div>
              <blockquote className="mt-4 whitespace-pre-line text-sm leading-6 text-[var(--ws-text-secondary)]">
                <Highlight text={detail.policy_text} span={detail.policy_span} />
              </blockquote>
            </div>
          ) : (
            <div className="workspace-empty-state">
              <h3 className="font-semibold">No matching policy text found</h3>
              <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">
                This is not proof that the organization has no relevant policy. Check the indexed documents and review the regulatory source.
              </p>
              <Link href={`/tenants/${tenantId}#policies`} className="workspace-text-link mt-3 inline-flex min-h-11 items-center">Review policy documents</Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
