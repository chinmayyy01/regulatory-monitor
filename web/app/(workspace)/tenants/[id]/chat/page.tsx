import Link from "next/link";
import { notFound } from "next/navigation";
import { Chat } from "@/components/Chat";
import { listTenants, requireToken } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ChatPage({
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
          Ask about regulation or your policies
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Answers cite the exact clause. If the corpus does not contain the
          answer, it says so.
        </p>
      </div>

      <Chat tenantId={tenantId} />
    </div>
  );
}
