export const metadata = { title: "Privacy — RegIntel" };

export default function PrivacyPage() {
  return (
    <div className="landing min-h-screen">
      <div className="mx-auto max-w-2xl space-y-6 px-6 py-16">
        <a href="/" className="app-link caption-2">
          ← RegIntel
        </a>
        <h1 className="heading-5 text-white">Privacy</h1>
        <p className="body-6 text-[#D4D4D4]">
          This is a demonstration deployment. Documents you upload are stored in the
          deployment's own Postgres database and are not shared with other tenants.
          Tenant isolation is enforced with database row level security.
        </p>
        <p className="body-6 text-[#D4D4D4]">
          Text extracted from your documents is embedded locally. When a verdict or an
          answer is generated, the relevant excerpts are sent to the configured model
          provider for that request. Documents are not used to train a model.
        </p>
        <p className="body-6 text-[#D4D4D4]">
          Authentication events (sign in, failures, sign out) are logged with an IP
          address and user agent for security purposes.
        </p>
        <p className="body-6 text-[#D4D4D4]">
          To have your data removed, delete the tenant's documents from the app or
          contact the operator of this deployment.
        </p>
      </div>
    </div>
  );
}
