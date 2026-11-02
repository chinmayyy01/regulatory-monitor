import Link from "next/link";
import { notFound } from "next/navigation";
import { GapCard } from "@/components/GapCard";
import { MapButton } from "@/components/MapButton";
import { UploadPolicy } from "@/components/UploadPolicy";
import { getGaps, listDocuments, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

const ORDER = ["satisfied", "partial", "stale", "missing"];

export default async function TenantPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ verdict?: string }>;
}) {
  const { id } = await params;
  const { verdict } = await searchParams;
  const active = ["satisfied", "partial", "stale", "missing"].includes(verdict ?? "")
    ? (verdict as string)
    : null;
  const tenantId = Number(id);
  if (!Number.isFinite(tenantId)) notFound();

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

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/app" className="text-xs text-slate-500 hover:text-slate-300">
            ← all tenants
          </Link>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-100">
            {tenant.name}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {tenant.entity_type}
            {tenant.products.length ? ` · ${tenant.products.join(", ")}` : ""} ·{" "}
            {tenant.documents} documents · {tenant.clauses} clauses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/tenants/${tenantId}/changes`}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200 transition hover:border-slate-600"
          >
            What changed
          </Link>
          <Link
            href={`/tenants/${tenantId}/chat`}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 transition hover:bg-emerald-400"
          >
            Ask a question
          </Link>
        </div>
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {ORDER.map((name) => (
          <Link
            key={name}
            href={`/tenants/${tenantId}${active === name ? "" : `?verdict=${name}`}`}
            className={`rounded-xl border p-4 transition ${
              active === name
                ? "border-emerald-500/50 bg-emerald-500/10"
                : "border-slate-800 bg-slate-900/40 hover:border-slate-700"
            }`}
          >
            <p className="text-xs uppercase tracking-wide text-slate-500">{name}</p>
            <p className="mt-1 text-2xl font-semibold text-slate-100">
              {summary[name] ?? 0}
            </p>
          </Link>
        ))}
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xs font-medium uppercase tracking-widest text-slate-500">
            Documents
          </h2>
          <MapButton tenantId={tenantId} />
        </div>

        <UploadPolicy tenantId={tenantId} />

        {documents.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-500">
            No documents yet. Upload a policy above.
          </p>
        ) : (
          <ul className="divide-y divide-slate-800 overflow-hidden rounded-xl border border-slate-800">
            {documents.map((document) => (
              <li
                key={document.id}
                className="flex items-center justify-between gap-4 bg-slate-900/30 px-4 py-3"
              >
                <div>
                  <p className="text-sm text-slate-200">{document.title}</p>
                  <p className="text-xs text-slate-500">
                    {document.doc_type} · {document.clauses} clauses ·{" "}
                    {document.page_count}p
                  </p>
                </div>
                <span className="text-xs text-slate-600">
                  {new Date(document.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-medium uppercase tracking-widest text-slate-500">
            Obligations
          </h2>
          {run_id ? (
            <span className="text-xs text-slate-600">run {run_id}</span>
          ) : null}
        </div>

        {total === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-500">
            No verdicts yet. Use “Re-check” after adding a document.
          </p>
        ) : (
          <>
            {active ? (
              <p className="text-xs text-slate-500">
                Showing {visible.length} {active} obligation
                {visible.length === 1 ? "" : "s"} ·{" "}
                <Link href={`/tenants/${tenantId}`} className="underline hover:text-slate-300">
                  clear filter
                </Link>
              </p>
            ) : null}
            <div className="space-y-3">
              {visible.map((gap) => (
                <GapCard key={gap.obligation_id} gap={gap} />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
