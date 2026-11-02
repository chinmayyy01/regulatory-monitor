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

  return (
    <div className="space-y-10">
      <section>
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-100">
            Compliance workspace
          </h1>
          <SignOutButton />
        </div>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          Which regulations bind you, which of your documents went stale, and what
          to edit. Every verdict is backed by a quote from both sides.
        </p>
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xs font-medium uppercase tracking-widest text-slate-500">
            Workspace
          </h2>
          <div className="flex flex-wrap items-center gap-3">
            <WorkspaceSwitcher memberships={memberships} activeId={activeId} />
            <NewWorkspace />
          </div>
        </div>
        {tenants.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-500">
            No tenants yet. Onboard one with{" "}
            <code className="text-slate-300">make tenant NAME=… DIR=…</code>.
          </p>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2">
            {tenants.map((tenant) => (
              <li key={tenant.id}>
                <Link
                  href={`/tenants/${tenant.id}`}
                  className="block rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition hover:border-slate-700 hover:bg-slate-900/70"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-100">{tenant.name}</span>
                    <span className="text-xs text-slate-500">
                      {tenant.entity_type}
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-slate-400">
                    {tenant.documents} documents · {tenant.clauses} clauses
                  </p>
                  {tenant.products.length > 0 ? (
                    <p className="mt-1 text-xs text-slate-500">
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
