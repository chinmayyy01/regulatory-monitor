"use client";

import { useState } from "react";
import type { AskResponse } from "@/lib/api";

const SUGGESTIONS = [
  "What is the capital adequacy requirement for commercial banks?",
  "How long do we have to resolve a customer complaint?",
  "What due diligence do we need before onboarding a vendor?",
];

export function Chat({ tenantId }: { tenantId: number }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(text: string) {
    const value = text.trim();
    if (!value || loading) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const response = await fetch(`/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenantId, question: value }),
      });
      if (!response.ok) throw new Error(`request failed (${response.status})`);
      setAnswer((await response.json()) as AskResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit(question);
        }}
        className="space-y-4"
      >
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={3}
          placeholder="Ask something the sources can answer…"
          className="input w-full resize-none rounded-xl p-4 text-sm"
        />
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setQuestion(suggestion);
                  void submit(suggestion);
                }}
                className="caption-2 rounded-full border border-[#313131] px-3 py-1 text-[#9B9B9B] transition hover:border-[#4A4A4A] hover:text-white"
              >
                {suggestion.length > 44 ? `${suggestion.slice(0, 44)}…` : suggestion}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={loading || question.trim().length < 3}
            className="btn-primary caption-1 rounded-full px-4 py-2 disabled:opacity-40"
          >
            {loading ? "Checking sources…" : "Ask"}
          </button>
        </div>
      </form>

      {error ? (
        <p className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-5 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {answer?.insufficient ? (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6">
          <p className="title-3 text-amber-200">Not enough evidence in the indexed documents.</p>
          <p className="caption-2 mt-2 text-amber-200/70">
            {answer.rejected} claim(s) dropped for unverifiable quotes, {answer.unsupported}{" "}
            claim(s) dropped because the quote did not support them.
          </p>
        </div>
      ) : null}

      {answer && !answer.insufficient ? (
        <ul className="space-y-4">
          {answer.claims.map((claim, index) => (
            <li key={index} className="surface rounded-2xl p-6">
              <p className="body-3 text-white">{claim.text}</p>
              <ul className="mt-4 space-y-3">
                {claim.citations.map((citation, citationIndex) => (
                  <li key={citationIndex} className="surface-2 rounded-lg p-4">
                    <span className="caption-4 text-[#6B6B6B]">{citation.label}</span>
                    <p className="caption-2 mt-2 text-[#D4D4D4]">“{citation.quote}”</p>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
