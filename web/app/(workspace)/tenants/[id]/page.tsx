import Link from "next/link";
import { notFound } from "next/navigation";
import { GapCard } from "@/components/GapCard";
import { MapButton } from "@/components/MapButton";
import { UploadPolicy } from "@/components/UploadPolicy";
import { getGaps, listDocuments, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_ORDER = ["missing", "partial", "stale", "satisfied"];
const STATUS_COPY: Record<string, { label: string; help: string }> = {
  missing: { label: "No matching clause", help: "Review the obligation and your policy." },
  partial: { label: "Needs a closer look", help: "The clause may cover only part of the requirement." },
  stale: { label: "May be out of date", help: "Check the current regulation and policy wording." },
  satisfied: { label: "Appears covered", help: "Confirm the cited wording is still current." },
};
const PAGE_SIZE = 10;

function entityLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default async function TenantPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ verdict?: string; page?: string }>;
}) {
  const { id } = await params;
  const { verdict, page: pageParam } = await searchParams;
  const tenantId = Number(id);
  if (!Number.isFinite(tenantId)) notFound();

  const active = STATUS_ORDER.includes(verdict ?? "") ? verdict! : null;
  const token = await requireToken();
  const tenants = await listTenants(token);
  const tenant = tenants.find((item) => item.id === tenantId);
  if (!tenant) notFound();

  const [{ summary, gaps }, documents] = await Promise.all([
    getGaps(tenantId, token),
    listDocuments(tenantId, token),
  ]);

  const needsReview = gaps
    .filter((gap) => gap.verdict !== "satisfied")
    .sort((a, b) => STATUS_ORDER.indexOf(a.verdict) - STATUS_ORDER.indexOf(b.verdict));
  const visible = active ? gaps.filter((gap) => gap.verdict === active) : needsReview;
  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const requested = Number(pageParam ?? "1");
  const current = Number.isFinite(requested)
    ? Math.min(Math.max(Math.floor(requested), 1), totalPages)
    : 1;
  const pageItems = visible.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);
  const totalAssessed = STATUS_ORDER.reduce((sum, status) => sum + (summary[status] ?? 0), 0);
  const totalNeedsReview = ["missing", "partial", "stale"].reduce(
    (sum, status) => sum + (summary[status] ?? 0),
    0,
  );
  const query = (nextPage: number) => {
    const params = new URLSearchParams();
    if (active) params.set("verdict", active);
    if (nextPage > 1) params.set("page", String(nextPage));
    const suffix = params.toString();
    return `/tenants/${tenantId}${suffix ? `?${suffix}` : ""}#obligations`;
  };

  return (
    <div className="workspace-page space-y-8">
      <section className="workspace-page-heading flex flex-wrap items-start justify-between gap-5">
        <div className="min-w-0">
          <p className="text-sm font-medium text-[var(--ws-muted)]">{entityLabel(tenant.entity_type)}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{tenant.name}</h1>
          <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">
            {tenant.products.length ? `Products: ${tenant.products.join(", ")} · ` : ""}
            {documents.length} policy document{documents.length === 1 ? "" : "s"}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href={`/tenants/${tenantId}/chat`} className="workspace-button workspace-button-secondary min-h-11 px-4">Ask a question</Link>
          <Link href={`/tenants/${tenantId}/changes`} className="workspace-button workspace-button-secondary min-h-11 px-4">View changes</Link>
        </div>
      </section>

      {documents.length === 0 ? (
        <section className="workspace-panel max-w-4xl p-5 sm:p-6" aria-labelledby="first-policy-title">
          <h2 id="first-policy-title" className="text-lg font-semibold">Start by adding your policies</h2>
          <p className="mt-2 max-w-2xl leading-6 text-[var(--ws-muted)]">
            Add the current policy PDFs for this organization. We’ll compare their text with applicable
            obligations and show the source wording so you can review each result.
          </p>
          <div className="mt-5"><UploadPolicy tenantId={tenantId} /></div>
        </section>
      ) : (
        <section aria-labelledby="assessment-title" className="workspace-panel p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 id="assessment-title" className="text-lg font-semibold">Assessment summary</h2>
              <p className="mt-1 max-w-2xl text-sm leading-5 text-[var(--ws-muted)]">
                {totalAssessed === 0
                  ? "Run a check to compare your policies with applicable obligations."
                  : `${summary.missing ?? 0} obligations have no matching policy clause in this assessment. Review the source evidence before deciding what to update.`}
              </p>
            </div>
            <MapButton tenantId={tenantId} count={10} />
          </div>
          <div className="workspace-status-grid mt-6" aria-label="Assessment results">
            {STATUS_ORDER.map((status) => {
              const copy = STATUS_COPY[status];
              const href = `/tenants/${tenantId}?verdict=${status}#obligations`;
              return (
                <Link key={status} href={href} className="workspace-status-item">
                  <span className="workspace-status-label">{copy.label}</span>
                  <span className="workspace-status-count">{summary[status] ?? 0}</span>
                  <span className="workspace-status-help">{copy.help}</span>
                </Link>
              );
            })}
          </div>
          <p className="mt-4 text-sm text-[var(--ws-muted)]">
            Results are decision support, not a legal compliance determination.
          </p>
        </section>
      )}

      <section id="obligations" className="workspace-section space-y-4" aria-labelledby="obligations-title">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="obligations-title" className="text-lg font-semibold">
              {active === "satisfied" ? "Results that appear covered" : "Obligations to review"}
            </h2>
            <p className="mt-1 text-sm text-[var(--ws-muted)]">
              {active
                ? `Showing ${visible.length} of ${summary[active] ?? 0} results · ${STATUS_COPY[active].label}`
                : `Showing ${needsReview.length} of ${totalNeedsReview} results without a confirmed policy match`}
            </p>
          </div>
          {active ? (
            <Link href={`/tenants/${tenantId}#obligations`} className="workspace-text-link min-h-11 inline-flex items-center">Show items to review</Link>
          ) : (
            <Link href={`/tenants/${tenantId}?verdict=satisfied#obligations`} className="workspace-text-link min-h-11 inline-flex items-center">View items that appear covered ({summary.satisfied ?? 0})</Link>
          )}
        </div>

        {documents.length === 0 ? (
          <div className="workspace-empty-state">
            <h3 className="font-semibold">Add policy documents to begin</h3>
            <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">Results appear after a policy check. Add the current policies for this organization first.</p>
            <Link href="#policies" className="workspace-text-link mt-3 inline-flex min-h-11 items-center">Go to policy documents</Link>
          </div>
        ) : totalAssessed === 0 ? (
          <div className="workspace-empty-state">
            <h3 className="font-semibold">No assessment yet</h3>
            <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">Run a policy check to create an evidence-backed list of results. The check reviews up to 10 obligations at a time.</p>
            <Link href="#policies" className="workspace-text-link mt-3 inline-flex min-h-11 items-center">Review uploaded policies</Link>
          </div>
        ) : pageItems.length === 0 ? (
          <div className="workspace-empty-state">
            <h3 className="font-semibold">Nothing to review in this group</h3>
            <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">Choose another result type above or return to the full review list.</p>
          </div>
        ) : (
          <>
            <ul className="space-y-3">
              {pageItems.map((gap) => <li key={gap.obligation_id}><GapCard gap={gap} tenantId={tenantId} /></li>)}
            </ul>
            {visible.length > PAGE_SIZE ? (
              <nav aria-label="Obligation pages" className="flex flex-wrap items-center justify-between gap-4 pt-2">
                <p className="text-sm text-[var(--ws-muted)]">
                  Showing {(current - 1) * PAGE_SIZE + 1}–{Math.min(current * PAGE_SIZE, visible.length)} of {visible.length}
                </p>
                <div className="flex gap-2">
                  {current > 1 ? <Link href={query(current - 1)} className="workspace-button workspace-button-secondary min-h-11 px-4">Previous</Link> : null}
                  {current < totalPages ? <Link href={query(current + 1)} className="workspace-button workspace-button-secondary min-h-11 px-4">Next</Link> : null}
                </div>
              </nav>
            ) : null}
          </>
        )}
      </section>

      <section id="policies" className="workspace-section space-y-4" aria-labelledby="policies-title">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="policies-title" className="text-lg font-semibold">Your policies</h2>
            <p className="mt-1 text-sm text-[var(--ws-muted)]">PDF documents used to compare against obligations.</p>
          </div>
          {documents.length > 0 ? <UploadPolicy tenantId={tenantId} compact /> : null}
        </div>
        {documents.length > 0 ? (
          <ul className="workspace-panel divide-y divide-[var(--ws-border)]">
            {documents.map((document) => (
              <li key={document.id} className="flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-5">
                <div className="min-w-0">
                  <p className="truncate font-medium">{document.title}</p>
                  <p className="mt-1 text-sm text-[var(--ws-muted)]">
                    {document.clauses} searchable section{document.clauses === 1 ? "" : "s"}
                    <span aria-hidden="true"> · </span>{document.page_count} page{document.page_count === 1 ? "" : "s"}
                    {document.effective_from ? <><span aria-hidden="true"> · </span>Effective {document.effective_from}</> : null}
                  </p>
                </div>
                <a
                  href={`/api/pdf?tenantId=${tenantId}&documentId=${document.id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="workspace-text-link min-h-11 inline-flex items-center"
                >
                  Open PDF <span className="sr-only">: {document.title}</span>
                </a>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
