import Link from "next/link";

export const metadata = { title: "Privacy — RegIntel" };

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 py-6 text-sm leading-6 text-slate-300">
      <Link href="/" className="text-xs text-slate-500 hover:text-slate-300">
        ← RegIntel
      </Link>
      <h1 className="text-2xl font-semibold text-slate-100">Privacy</h1>
      <p>
        This is a demonstration deployment. Documents you upload are stored in the
        deployment's own Postgres database and are not shared with other tenants.
        Tenant isolation is enforced with database row level security.
      </p>
      <p>
        Text extracted from your documents is embedded locally. When a verdict or
        an answer is generated, the relevant excerpts are sent to the configured
        model provider for that request. Documents are not used to train a model.
      </p>
      <p>
        Authentication events (sign in, failures, sign out) are logged with an IP
        address and user agent for security purposes.
      </p>
      <p>
        To have your data removed, delete the tenant's documents from the app or
        contact the operator of this deployment.
      </p>
    </div>
  );
}
