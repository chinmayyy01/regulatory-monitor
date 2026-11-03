import Link from "next/link";
import { NewWorkspace } from "@/components/NewWorkspace";
import { SignOutButton } from "@/components/SignOutButton";
import { WorkspaceSwitcher } from "@/components/WorkspaceSwitcher";
import { listMemberships, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const token = await requireToken();
  const [tenants, memberships] = await Promise.all([
    listTenants(token),
    listMemberships(token),
  ]);
  const activeId = tenants[0]?.id ?? 0;
  const authDisabled = process.env.AUTH_DISABLED === "true";

  return (
    <div className="space-y-12">
      <section>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <h1 className="heading-4 text-white">Workspace</h1>
          {authDisabled ? null : <SignOutButton />}
        </div>
        <p className="body-3 muted mt-3 max-w-[680px]">
          Which regulations bind you, which of your documents went stale, and what
          to edit. Every verdict is backed by a quote from both sides.
        </p>
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="caption-4 uppercase tracking-wide text-[#6B6B6B]">
            Your entities
          </h2>
          <div className="flex flex-wrap items-center gap-4">
            <WorkspaceSwitcher memberships={memberships} activeId={activeId} />
            <NewWorkspace />
          </div>
        </div>

        {tenants.length === 0 ? (
          <p className="surface rounded-2xl p-6 body-6 muted">
            No workspace yet. Create one above, then upload a policy.
          </p>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2">
            {tenants.map((tenant) => (
              <li key={tenant.id}>
                <Link
                  href={`/tenants/${tenant.id}`}
                  className="surface block rounded-2xl p-6 transition hover:border-[#4A4A4A]"
                >
                  <div className="flex items-center justify-between gap-4">
                    <span className="title-1 text-white">{tenant.name}</span>
                    <span className="caption-2 muted">{tenant.entity_type}</span>
                  </div>
                  <p className="caption-1 muted mt-4">
                    {tenant.documents} documents · {tenant.clauses} clauses
                  </p>
                  {tenant.products.length > 0 ? (
                    <p className="caption-4 mt-2 text-[#6B6B6B]">
                      {tenant.products.join(", ")}
                    </p>
                  ) : null}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
