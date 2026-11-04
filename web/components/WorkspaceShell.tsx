"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { SignOutButton } from "@/components/SignOutButton";

type WorkspaceShellProps = {
  children: React.ReactNode;
  authDisabled: boolean;
};

export function WorkspaceShell({ children, authDisabled }: WorkspaceShellProps) {
  const pathname = usePathname();
  const tenantId = pathname.match(/^\/tenants\/(\d+)/)?.[1];
  const [hash, setHash] = useState("");

  useEffect(() => {
    const updateHash = () => setHash(window.location.hash);
    updateHash();
    window.addEventListener("hashchange", updateHash);
    return () => window.removeEventListener("hashchange", updateHash);
  }, []);

  const links = tenantId
    ? [
        { label: "Overview", href: `/tenants/${tenantId}`, hash: "" },
        { label: "Obligations", href: `/tenants/${tenantId}#obligations`, hash: "#obligations" },
        { label: "Policies", href: `/tenants/${tenantId}#policies`, hash: "#policies" },
        { label: "Changes", href: `/tenants/${tenantId}/changes`, hash: "" },
        { label: "Ask a question", href: `/tenants/${tenantId}/chat`, hash: "" },
      ]
    : [{ label: "Your workspaces", href: "/app", hash: "" }];

  function isActive(href: string, itemHash: string) {
    if (itemHash) return pathname === `/tenants/${tenantId}` && hash === itemHash;
    if (href === `/tenants/${tenantId}`) {
      return (pathname === href && !hash) || pathname.startsWith(`${href}/obligations/`);
    }
    return pathname === href;
  }

  function closeMenu(event: React.MouseEvent<HTMLAnchorElement>) {
    event.currentTarget.closest("details")?.removeAttribute("open");
  }

  return (
    <div className="workspace-app min-h-screen">
      <a href="#main-content" className="workspace-skip-link">Skip to main content</a>
      <aside className="workspace-sidebar fixed inset-y-0 left-0 z-20 hidden w-[232px] flex-col border-r md:flex">
        <Link href="/app" className="workspace-brand flex items-center gap-3 px-6 py-6">
          <span aria-hidden="true" className="workspace-mark">R</span>
          <span className="text-base font-semibold tracking-tight">RegIntel</span>
        </Link>
        <p className="px-6 pb-4 text-sm text-[var(--ws-muted)]">Compliance workspace</p>
        <nav aria-label="Main navigation" className="px-3">
          <ul className="space-y-1">
            {links.map((link) => {
              const active = isActive(link.href, link.hash);
              return (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    onClick={() => setHash(link.hash)}
                    aria-current={active ? "page" : undefined}
                    className={`workspace-nav-link ${active ? "is-active" : ""}`}
                  >
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="mt-auto border-t border-[var(--ws-border)] p-5">
          <p className="text-sm leading-5 text-[var(--ws-muted)]">
            Evidence-led information, not legal advice.
          </p>
        </div>
      </aside>

      <div className="md:pl-[232px]">
        <header className="workspace-topbar sticky top-0 z-10 flex min-h-14 items-center justify-between border-b px-4 sm:px-6 lg:px-8 md:min-h-16">
          <Link href="/app" className="flex items-center gap-3 md:hidden">
            <span aria-hidden="true" className="workspace-mark">R</span>
            <span className="font-semibold">RegIntel</span>
          </Link>
          <p className="hidden text-sm text-[var(--ws-muted)] md:block">
            {tenantId ? "Regulatory obligations and policy evidence" : "Your organizations"}
          </p>
          <div className="flex items-center gap-3">
            {authDisabled ? (
              <span className="workspace-demo-note">Demo mode · don’t upload sensitive documents</span>
            ) : null}
            {!authDisabled ? <div className="hidden md:block"><SignOutButton /></div> : null}
            <details className="workspace-mobile-menu relative md:hidden">
              <summary className="workspace-button workspace-button-secondary min-h-11 cursor-pointer list-none px-4 py-2">
                Menu
              </summary>
              <nav aria-label="Main navigation" className="workspace-mobile-sheet absolute right-0 top-14 z-30 w-[min(88vw,340px)] p-3">
                <ul className="space-y-1">
                  {links.map((link) => {
                    const active = isActive(link.href, link.hash);
                    return (
                      <li key={link.label}>
                        <Link
                          href={link.href}
                          onClick={(event) => {
                            setHash(link.hash);
                            closeMenu(event);
                          }}
                          aria-current={active ? "page" : undefined}
                          className={`workspace-nav-link ${active ? "is-active" : ""}`}
                        >
                          {link.label}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
                {authDisabled ? (
                  <p className="mt-3 border-t border-[var(--ws-border)] px-3 pt-3 text-sm leading-5 text-[var(--ws-muted)]">
                    Demo mode · don’t upload sensitive documents
                  </p>
                ) : (
                  <div className="mt-3 border-t border-[var(--ws-border)] px-3 pt-3"><SignOutButton /></div>
                )}
              </nav>
            </details>
          </div>
        </header>
        <main id="main-content" className="mx-auto w-full max-w-[1500px] px-4 py-7 sm:px-6 sm:py-9 lg:px-9">
          {children}
        </main>
      </div>
    </div>
  );
}
