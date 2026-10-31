import { redirect } from "next/navigation";
import { LoginForm } from "@/components/LoginForm";
import { sessionToken } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  if (await sessionToken()) {
    redirect("/");
  }

  return (
    <div className="mx-auto max-w-md space-y-8 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
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
