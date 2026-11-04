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
    <div className="workspace-page max-w-5xl space-y-7">
      <div>
        <Link href={`/tenants/${tenantId}`} className="workspace-text-link min-h-11 inline-flex items-center">
          ← Back to {tenant.name}
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Ask about obligations</h1>
        <p className="mt-2 max-w-3xl text-base leading-6 text-[var(--ws-muted)]">
          Ask in plain language about RBI requirements or this workspace’s policies. Every answer includes source text; if there isn’t enough evidence, no answer is shown.
        </p>
      </div>

      <Chat tenantId={tenantId} />
    </div>
  );
}
