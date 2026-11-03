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
    <div className="space-y-10">
      <div>
        <Link href={`/tenants/${tenantId}`} className="app-link caption-2">
          ← {tenant.name}
        </Link>
        <h1 className="heading-4 mt-3 text-white">Ask about regulation or your policies</h1>
        <p className="body-6 muted mt-3 max-w-[680px]">
          Answers cite the exact clause. If the corpus does not contain the answer, it
          says so.
        </p>
      </div>

      <Chat tenantId={tenantId} />
    </div>
  );
}
