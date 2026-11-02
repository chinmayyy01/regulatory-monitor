import Link from "next/link";
import { notFound } from "next/navigation";
import { listChanges, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

const TONE: Record<string, string> = {
  worsened: "text-rose-300",
  improved: "text-emerald-300",
  new: "text-sky-300",
  dropped: "text-slate-400",
};

export default async function ChangesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const tenantId = Number(id);
  const token = await requireToken();
  const tenants = await listTenants(token);
  const tenant = tenants.find((item) => item.id === tenantId);
  if (!tenant) notFound();

  const { changes, from_run, to_run } = await listChanges(tenantId, token);

  return (
    <div className="space-y-8">
      <div>
        <Link
          href={`/tenants/${tenantId}`}
          className="text-xs text-slate-500 hover:text-slate-300"
        >
          ← {tenant.name}
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-100">
          What changed
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          {from_run
            ? `Comparing run ${from_run} with ${to_run}.`
            : "At least two mapping runs are needed before a diff exists."}
        </p>
      </div>

      {changes.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-500">
          No verdicts changed between these runs.
        </p>
      ) : (
        <ul className="space-y-3">
          {changes.map((change) => (
            <li
              key={change.obligation_id}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <div className="flex items-center gap-3">
                <span className={`text-xs font-medium uppercase tracking-wide ${TONE[change.direction] ?? "text-slate-300"}`}>
                  {change.direction}
                </span>
                <span className="text-xs text-slate-500">
                  {change.before ?? "—"} → {change.after ?? "—"}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-200">
                {change.action || `obligation ${change.obligation_id}`}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
