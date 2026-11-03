import Link from "next/link";
import { notFound } from "next/navigation";
import { listChanges, listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

const TONE: Record<string, string> = {
  worsened: "text-rose-300",
  improved: "text-emerald-300",
  new: "text-white",
  dropped: "text-[#9B9B9B]",
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
    <div className="space-y-10">
      <div>
        <Link href={`/tenants/${tenantId}`} className="app-link caption-2">
          ← {tenant.name}
        </Link>
        <h1 className="heading-4 mt-3 text-white">What changed</h1>
        <p className="body-6 muted mt-3">
          {from_run
            ? `Comparing run ${from_run} with ${to_run}.`
            : "At least two mapping runs are needed before a diff exists."}
        </p>
      </div>

      {changes.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-[#313131] p-6 body-6 muted">
          No verdicts changed between these runs.
        </p>
      ) : (
        <ul className="space-y-3">
          {changes.map((change) => (
            <li key={change.obligation_id} className="surface rounded-2xl p-6">
              <div className="flex flex-wrap items-center gap-4">
                <span className={`caption-4 uppercase tracking-wide ${TONE[change.direction] ?? "muted"}`}>
                  {change.direction}
                </span>
                <span className="caption-2 muted">
                  {change.before ?? "—"} → {change.after ?? "—"}
                </span>
              </div>
              <p className="body-3 mt-3 text-white">
                {change.action || `obligation ${change.obligation_id}`}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
