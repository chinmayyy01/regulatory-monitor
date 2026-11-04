import Link from "next/link";
import { notFound } from "next/navigation";
import { listChanges, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

const DIRECTION: Record<string, { label: string; className: string }> = {
  worsened: { label: "Needs attention", className: "workspace-change-worsened" },
  improved: { label: "Improved", className: "workspace-change-improved" },
  new: { label: "New result", className: "workspace-change-new" },
  dropped: { label: "No longer in this assessment", className: "workspace-change-neutral" },
};

const VERDICT: Record<string, string> = {
  satisfied: "Appears covered",
  partial: "Partial match",
  missing: "No matching clause",
  stale: "May be out of date",
};

export default async function ChangesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tenantId = Number(id);
  if (!Number.isFinite(tenantId)) notFound();
  const token = await requireToken();
  const tenants = await listTenants(token);
  const tenant = tenants.find((item) => item.id === tenantId);
  if (!tenant) notFound();

  const { changes, from_run, to_run } = await listChanges(tenantId, token);

  return (
    <div className="workspace-page space-y-7">
      <section>
        <p className="text-sm text-[var(--ws-muted)]">{tenant.name}</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Assessment changes</h1>
        <p className="mt-2 max-w-2xl text-base leading-6 text-[var(--ws-muted)]">
          See which results changed between your latest policy checks. A change is a reason to review the evidence, not a final compliance decision.
        </p>
        {from_run ? <p className="mt-3 text-sm text-[var(--ws-muted)]">Comparing assessment {from_run} with {to_run}.</p> : null}
      </section>

      {changes.length === 0 ? (
        <section className="workspace-empty-state max-w-3xl">
          <h2 className="font-semibold">{from_run ? "No results changed" : "A second check is needed"}</h2>
          <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">
            {from_run
              ? "The latest two checks returned the same verdicts. Changes will appear here when a result differs."
              : "Run another policy check to compare results over time. The change feed appears after two checks."}
          </p>
          <Link href={`/tenants/${tenantId}`} className="workspace-button workspace-button-secondary mt-4 inline-flex min-h-11 items-center px-4">
            Return to overview
          </Link>
        </section>
      ) : (
        <section aria-labelledby="changes-list-title" className="space-y-4">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 id="changes-list-title" className="text-lg font-semibold">{changes.length} changed result{changes.length === 1 ? "" : "s"}</h2>
            <p className="text-sm text-[var(--ws-muted)]">From {from_run} to {to_run}</p>
          </div>
          <ul className="space-y-3">
            {changes.map((change) => {
              const direction = DIRECTION[change.direction] ?? DIRECTION.new;
              const before = change.before ? VERDICT[change.before] ?? change.before : "Not in previous check";
              const after = change.after ? VERDICT[change.after] ?? change.after : "Not in current check";
              return (
                <li key={change.obligation_id} className="workspace-panel p-4 sm:p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className={`workspace-change-label ${direction.className}`}>{direction.label}</span>
                    <span className="text-sm text-[var(--ws-muted)]">{before} <span aria-label="changed to">→</span> {after}</span>
                  </div>
                  <p className="mt-3 font-medium leading-6">{change.action || "Regulatory obligation"}</p>
                  <Link href={`/tenants/${tenantId}/obligations/${change.obligation_id}`} className="workspace-text-link mt-2 inline-flex min-h-11 items-center">
                    Review evidence <span className="sr-only"> for {change.action}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
