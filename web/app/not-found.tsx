import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-start gap-6 py-16">
      <p className="text-xs uppercase tracking-widest text-slate-500">404</p>
      <h1 className="text-2xl font-semibold text-slate-100">
        That page is not here.
      </h1>
      <p className="text-sm leading-6 text-slate-400">
        The link may be old, or the tenant may belong to another workspace.
      </p>
      <div className="flex gap-3">
        <Link
          href="/app"
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950"
        >
          Go to workspace
        </Link>
        <Link
          href="/"
          className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-200"
        >
          About RegIntel
        </Link>
      </div>
    </div>
  );
}
