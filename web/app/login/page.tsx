import { redirect } from "next/navigation";
import { LoginForm } from "@/components/LoginForm";
import { currentUser, sessionToken } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  const token = await sessionToken();
  if (token && (await currentUser(token))) {
    redirect("/app");
  }

  return (
    <div className="mx-auto max-w-md space-y-8 py-10">
      <div>
        <a href="/" className="text-xs text-slate-500 hover:text-slate-300">
          ← RegIntel
        </a>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-100">
          Sign in
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Your workspace is scoped to one tenant.
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
