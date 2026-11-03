import Link from "next/link";

export default function NotFound() {
  return (
    <div className="landing min-h-screen">
      <div className="mx-auto flex max-w-md flex-col items-start gap-6 px-6 py-24">
        <p className="caption-4 uppercase tracking-widest text-[#6B6B6B]">404</p>
        <h1 className="heading-5 text-white">That page is not here.</h1>
        <p className="body-6 muted">
          The link may be old, or the tenant may belong to another workspace.
        </p>
        <div className="flex gap-3">
          <Link href="/app" className="btn-primary caption-1 rounded-full px-4 py-2">
            Go to workspace
          </Link>
          <Link href="/" className="btn-ghost caption-1 rounded-full px-4 py-2">
            About RegIntel
          </Link>
        </div>
      </div>
    </div>
  );
}
