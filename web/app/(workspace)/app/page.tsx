import Link from "next/link";
import { NewWorkspace } from "@/components/NewWorkspace";
import { WorkspaceSwitcher } from "@/components/WorkspaceSwitcher";
import { listMemberships, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

function entityLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default async function HomePage() {
  const token = await requireToken();
  const [tenants, memberships] = await Promise.all([
    listTenants(token),
    listMemberships(token),
  ]);
  const activeId = tenants[0]?.id ?? 0;

  return (
    <div className="workspace-page space-y-8">
      <section className="workspace-page-heading flex flex-wrap items-end justify-between gap-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your workspaces</h1>
          <p className="mt-2 max-w-2xl text-base leading-6 text-[var(--ws-muted)]">
            Each workspace holds one organization’s policies and regulatory assessment.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-3">
          <WorkspaceSwitcher memberships={memberships} activeId={activeId} />
          <NewWorkspace />
        </div>
      </section>

      {tenants.length === 0 ? (
        <section className="workspace-panel max-w-3xl p-6 sm:p-8" aria-labelledby="start-title">
          <h2 id="start-title" className="text-lg font-semibold">Start with an organization</h2>
          <p className="mt-2 max-w-2xl leading-6 text-[var(--ws-muted)]">
            Create a workspace for the regulated entity you support. Then add its policy PDFs so
            RegIntel can compare them with applicable obligations.
          </p>
          <ol className="mt-6 grid gap-4 sm:grid-cols-3">
            <li className="workspace-step"><strong>Create a workspace</strong><span>Name the organization and choose its entity type.</span></li>
            <li className="workspace-step"><strong>Add policy documents</strong><span>Upload readable PDFs, up to 10 MB each.</span></li>
            <li className="workspace-step"><strong>Review the evidence</strong><span>Check each result against the original source text.</span></li>
          </ol>
        </section>
      ) : (
        <section aria-labelledby="workspace-list-title" className="space-y-4">
          <div className="flex items-baseline justify-between gap-4">
            <h2 id="workspace-list-title" className="text-lg font-semibold">Organizations</h2>
            <p className="text-sm text-[var(--ws-muted)]">{tenants.length} workspace{tenants.length === 1 ? "" : "s"}</p>
          </div>
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {tenants.map((tenant) => (
              <li key={tenant.id}>
                <Link href={`/tenants/${tenant.id}`} className="workspace-panel workspace-tenant-link block h-full p-5 sm:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <h3 className="text-lg font-semibold">{tenant.name}</h3>
                    <span className="workspace-type-label">{entityLabel(tenant.entity_type)}</span>
                  </div>
                  <p className="mt-5 text-sm text-[var(--ws-muted)]">
                    {tenant.documents} policy document{tenant.documents === 1 ? "" : "s"}
                    <span aria-hidden="true"> · </span>
                    {tenant.clauses} searchable sections
                  </p>
                  {tenant.products.length ? (
                    <p className="mt-2 text-sm text-[var(--ws-muted)]">Products: {tenant.products.join(", ")}</p>
                  ) : null}
                  <span className="mt-6 inline-flex min-h-11 items-center font-medium text-[var(--ws-accent)]">
                    Open workspace <span className="ml-2" aria-hidden="true">→</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
