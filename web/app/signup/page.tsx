import { redirect } from "next/navigation";
import { SignupForm } from "@/components/SignupForm";
import { currentUser, sessionToken } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SignupPage() {
  if (process.env.AUTH_DISABLED === "true") {
    redirect("/app");
  }
  const token = await sessionToken();
  if (token && (await currentUser(token))) {
    redirect("/app");
  }

  return (
    <div className="landing min-h-screen">
      <div className="mx-auto max-w-md space-y-8 px-6 py-16">
        <div>
          <a href="/" className="app-link caption-2">
            ← RegIntel
          </a>
          <h1 className="heading-5 mt-4 text-white">Create a workspace</h1>
          <p className="body-6 muted mt-3">
            One workspace per regulated entity. You land on an empty workspace and can
            upload your first policy immediately.
          </p>
        </div>
        <SignupForm googleEnabled={Boolean(process.env.GOOGLE_CLIENT_ID)} />
      </div>
    </div>
  );
}
