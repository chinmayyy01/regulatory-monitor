export default function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="landing min-h-screen">
      <header className="border-b border-[#272727]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <a href="/app" className="flex items-center gap-3">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-white text-sm font-semibold text-black">
              R
            </span>
            <span className="title-3 text-white">RegIntel</span>
          </a>
          <div className="flex items-center gap-6">
            <a href="/" className="app-link caption-2">
              About
            </a>
            <span className="caption-2 muted">informational, not legal advice</span>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  );
}
