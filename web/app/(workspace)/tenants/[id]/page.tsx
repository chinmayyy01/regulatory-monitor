import Link from "next/link";
import { notFound } from "next/navigation";
import { GapCard } from "@/components/GapCard";
import { MapButton } from "@/components/MapButton";
import { UploadPolicy } from "@/components/UploadPolicy";
import { getGaps, listDocuments, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

const ORDER = ["satisfied", "partial", "stale", "missing"];
const PAGE_SIZE = 15;

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

  const active = ["satisfied", "partial", "stale", "missing"].includes(verdict ?? "")
    ? (verdict as string)
    : null;

  const token = await requireToken();
  const tenants = await listTenants(token);
  const tenant = tenants.find((item) => item.id === tenantId);
  if (!tenant) notFound();

  const [{ summary, gaps, run_id }, documents] = await Promise.all([
    getGaps(tenantId, token),
    listDocuments(tenantId, token),
  ]);

  const total = Object.values(summary).reduce((sum, value) => sum + value, 0);
  const visible = active ? gaps.filter((gap) => gap.verdict === active) : gaps;
  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const requested = Number(pageParam ?? "1");
  const current = Number.isFinite(requested)
    ? Math.min(Math.max(Math.floor(requested), 1), totalPages)
    : 1;
  const pageItems = visible.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);
  const query = (nextPage: number) => {
    const params = new URLSearchParams();
    if (active) params.set("verdict", active);
    if (nextPage > 1) params.set("page", String(nextPage));
    const suffix = params.toString();
    return `/tenants/${tenantId}${suffix ? `?${suffix}` : ""}`;
  };

  return (
    <div className="space-y-12">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <Link href="/app" className="app-link caption-2">
            ← workspaces
          </Link>
          <h1 className="heading-4 mt-3 text-white">{tenant.name}</h1>
          <p className="caption-1 muted mt-2">
            {tenant.entity_type}
            {tenant.products.length ? ` · ${tenant.products.join(", ")}` : ""} ·{" "}
            {tenant.documents} documents · {tenant.clauses} clauses
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`/tenants/${tenantId}/changes`} className="btn-ghost caption-1 rounded-full px-4 py-2">
            What changed
          </Link>
          <Link href={`/tenants/${tenantId}/chat`} className="btn-primary caption-1 rounded-full px-4 py-2">
            Ask a question
          </Link>
        </div>
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {ORDER.map((name) => (
          <Link
            key={name}
            href={`/tenants/${tenantId}${active === name ? "" : `?verdict=${name}`}`}
            className={`rounded-2xl border p-6 transition ${
              active === name
                ? "border-white/40 bg-white/10"
                : "border-[#272727] bg-[#181818] hover:border-[#4A4A4A]"
            }`}
          >
            <p className="caption-4 uppercase tracking-wide text-[#6B6B6B]">{name}</p>
            <p className="heading-5 mt-2 text-white">{summary[name] ?? 0}</p>
          </Link>
        ))}
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="caption-4 uppercase tracking-wide text-[#6B6B6B]">Documents</h2>
          <MapButton tenantId={tenantId} />
        </div>

        <UploadPolicy tenantId={tenantId} />

        {documents.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-[#313131] p-6 body-6 muted">
            No documents yet. Upload a policy above.
          </p>
        ) : (
          <ul className="surface divide-y divide-[#272727] overflow-hidden rounded-2xl">
            {documents.map((document) => (
              <li key={document.id} className="flex items-center justify-between gap-4 px-6 py-4">
                <div>
                  <p className="title-3 text-white">{document.title}</p>
                  <p className="caption-2 muted mt-1">
                    {document.doc_type} · {document.clauses} clauses · {document.page_count}p
                  </p>
                </div>
                <a
                  href={`/api/pdf?tenantId=${tenantId}&documentId=${document.id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="app-link caption-1"
                >
                  open
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="caption-4 uppercase tracking-wide text-[#6B6B6B]">Obligations</h2>
          {run_id ? <span className="caption-4 text-[#6B6B6B]">run {run_id}</span> : null}
        </div>

        {total === 0 ? (
          <p className="rounded-2xl border border-dashed border-[#313131] p-6 body-6 muted">
            No verdicts yet. Upload a policy and use re-check.
          </p>
        ) : (
          <>
            {active ? (
              <p className="caption-2 muted">
                Showing {visible.length} {active} obligation{visible.length === 1 ? "" : "s"} ·{" "}
                <Link href={`/tenants/${tenantId}`} className="underline hover:text-white">
                  clear filter
                </Link>
              </p>
            ) : null}
            <div className="space-y-4">
              {pageItems.map((gap) => (
                <GapCard key={gap.obligation_id} gap={gap} tenantId={tenantId} />
              ))}
            </div>
            {visible.length > PAGE_SIZE ? (
              <div className="flex items-center justify-between gap-4 pt-2">
                <p className="caption-2 muted">
                  {(current - 1) * PAGE_SIZE + 1} to {Math.min(current * PAGE_SIZE, visible.length)} of{" "}
                  {visible.length}
                </p>
                <div className="flex items-center gap-2">
                  {current > 1 ? (
                    <Link href={query(current - 1)} className="btn-ghost caption-1 rounded-full px-3 py-1.5">
                      Previous
                    </Link>
                  ) : null}
                  {current < totalPages ? (
                    <Link href={query(current + 1)} className="btn-ghost caption-1 rounded-full px-3 py-1.5">
                      Next
                    </Link>
                  ) : null}
                </div>
              </div>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
