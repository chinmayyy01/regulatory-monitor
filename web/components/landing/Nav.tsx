"use client";

import { useEffect, useState } from "react";

const LINKS = [
  { href: "#benefits", label: "Benefits" },
  { href: "#how", label: "How it works" },
  { href: "#faq", label: "Questions" },
];

export function Nav() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <nav
        aria-label="Primary"
        className="fixed left-1/2 top-4 z-40 flex -translate-x-1/2 items-center gap-2 rounded-full border border-[#313131] bg-[#181818]/70 px-3 py-2 backdrop-blur-xl"
      >
        <a href="/" className="title-3 px-2 text-white">
          RegIntel
        </a>
        <span className="hidden h-4 w-px bg-[#313131] sm:block" aria-hidden />
        <ul className="hidden items-center gap-1 sm:flex">
          {LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="title-4 rounded-full px-3 py-2 text-[#9B9B9B] transition-colors duration-300 hover:bg-[#272727] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white active:translate-y-px"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>
        <a
          href="/login"
          className="button-md rounded-full bg-white px-3 py-2 text-black transition-transform duration-300 hover:scale-[1.02] active:scale-[0.98] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        >
          Sign in
        </a>
        <button
          type="button"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
          className="relative h-8 w-8 rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white sm:hidden"
        >
          <span
            className={`absolute left-1/2 top-1/2 h-px w-4 bg-white transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              open ? "rotate-45" : "-translate-y-1"
            } -translate-x-1/2`}
          />
          <span
            className={`absolute left-1/2 top-1/2 h-px w-4 bg-white transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              open ? "-rotate-45" : "translate-y-1"
            } -translate-x-1/2`}
          />
        </button>
      </nav>

      <div
        className={`fixed inset-0 z-30 bg-[#000000]/95 backdrop-blur-2xl transition-opacity duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] sm:hidden ${
          open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        <ul className="flex h-full flex-col justify-center gap-6 px-10">
          {LINKS.map((link, index) => (
            <li
              key={link.href}
              className={`transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                open ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
              }`}
              style={{ transitionDelay: open ? `${index * 60}ms` : "0ms" }}
            >
              <a
                href={link.href}
                onClick={() => setOpen(false)}
                className="heading-4 text-white"
              >
                {link.label}
              </a>
            </li>
          ))}
          <li
            className={`transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              open ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
            }`}
            style={{ transitionDelay: open ? `${LINKS.length * 60}ms` : "0ms" }}
          >
            <a href="/login" className="heading-4 text-white">
              Sign in
            </a>
          </li>
        </ul>
      </div>
    </>
  );
}
