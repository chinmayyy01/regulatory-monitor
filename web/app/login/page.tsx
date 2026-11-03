import { redirect } from "next/navigation";
import { LoginForm } from "@/components/LoginForm";
import { currentUser, sessionToken } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (process.env.AUTH_DISABLED === "true") {
    redirect("/app");
  }
  const token = await sessionToken();
  if (token && (await currentUser(token))) {
    redirect("/app");
  }
  const { error } = await searchParams;

  return (
    <div className="landing min-h-screen">
      <div className="mx-auto max-w-md space-y-8 px-6 py-16">
        <div>
          <a href="/" className="app-link caption-2">
            ← RegIntel
          </a>
          <h1 className="heading-5 mt-4 text-white">Sign in</h1>
          <p className="body-6 muted mt-3">Your workspace is scoped to one entity.</p>
        </div>

        {error ? (
          <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
            {error}
          </p>
        ) : null}

        <LoginForm googleEnabled={Boolean(process.env.GOOGLE_CLIENT_ID)} />

        <p className="caption-2 muted text-center">
          No account yet?{" "}
          <a href="/signup" className="underline hover:text-white">
            Create a workspace
          </a>
        </p>
      </div>
    </div>
  );
}
