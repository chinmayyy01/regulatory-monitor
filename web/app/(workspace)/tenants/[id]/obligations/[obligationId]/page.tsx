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
    <div className="space-y-10">
      <div>
        <Link href={`/tenants/${tenantId}`} className="app-link caption-2">
          ← {tenant.name}
        </Link>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="caption-4 uppercase tracking-wide text-[#6B6B6B]">
              {detail.modality} {detail.condition ? `· ${detail.condition}` : ""}
            </p>
            <h1 className="heading-4 mt-3 max-w-[680px] text-white">{detail.action}</h1>
          </div>
          {detail.verdict ? <VerdictBadge verdict={detail.verdict} /> : null}
        </div>
        {detail.scope_entities.length ? (
          <p className="caption-2 muted mt-4">applies to: {detail.scope_entities.join(", ")}</p>
        ) : null}
        {detail.reason ? <p className="body-6 mt-4 max-w-[680px] text-[#D4D4D4]">{detail.reason}</p> : null}
      </div>

      <section className="space-y-3">
        <h2 className="caption-4 uppercase tracking-wide text-[#6B6B6B]">Regulation</h2>
        <div className="surface rounded-2xl p-6">
          <p className="caption-2 muted">
            {detail.regulation_title}
            {detail.regulation_section ? ` · s.${detail.regulation_section}` : ""}
            {detail.regulation_page ? ` · page ${detail.regulation_page}` : ""}
          </p>
          <p className="body-6 mt-4 whitespace-pre-line text-[#D4D4D4]">{detail.regulation_text}</p>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="caption-4 uppercase tracking-wide text-[#6B6B6B]">Your policy</h2>
        {detail.policy_text ? (
          <div className="surface rounded-2xl p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="caption-2 muted">
                {detail.policy_title}
                {detail.policy_section ? ` · s.${detail.policy_section}` : ""}
                {detail.policy_page ? ` · page ${detail.policy_page}` : ""}
              </p>
              {detail.policy_document_id && detail.policy_page ? (
                <a
                  href={`/api/pdf?tenantId=${tenantId}&documentId=${detail.policy_document_id}#page=${detail.policy_page}`}
                  target="_blank"
                  rel="noreferrer"
                  className="app-link caption-1 underline"
                >
                  source page {detail.policy_page}
                </a>
              ) : null}
            </div>
            <p className="body-6 mt-4 whitespace-pre-line text-[#D4D4D4]">
              <Highlight text={detail.policy_text} span={detail.policy_span} />
            </p>
          </div>
        ) : (
          <p className="rounded-2xl border border-dashed border-[#313131] p-6 body-6 muted">
            No clause in your policies addresses this obligation.
          </p>
        )}
      </section>
    </div>
  );
}
