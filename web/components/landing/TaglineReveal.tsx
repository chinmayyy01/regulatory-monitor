"use client";

import { useEffect, useRef } from "react";

export function TaglineReveal({ text }: { text: string }) {
  const refs = useRef<(HTMLSpanElement | null)[]>([]);
  const words = text.split(" ");

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      refs.current.forEach((node) => node?.classList.add("on"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("on");
            observer.unobserve(entry.target);
          }
        }
      },
      { rootMargin: "-45% 0px -45% 0px", threshold: 0 },
    );
    refs.current.forEach((node) => {
      if (node) observer.observe(node);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <p className="heading-2 balance max-w-[680px]">
      {words.map((word, index) => (
        <span
          key={`${word}-${index}`}
          ref={(node) => {
            refs.current[index] = node;
          }}
          className="tagline-word"
        >
          {word}
          {index < words.length - 1 ? " " : ""}
        </span>
      ))}
    </p>
  );
}
