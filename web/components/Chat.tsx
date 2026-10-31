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
    <div className="space-y-6">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit(question);
        }}
        className="space-y-3"
      >
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={3}
          placeholder="Ask something the sources can answer…"
          className="w-full resize-none rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-emerald-500/60"
        />
        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setQuestion(suggestion);
                  void submit(suggestion);
                }}
                className="rounded-full border border-slate-800 px-3 py-1 text-xs text-slate-400 transition hover:border-slate-700 hover:text-slate-200"
              >
                {suggestion.length > 44 ? `${suggestion.slice(0, 44)}…` : suggestion}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={loading || question.trim().length < 3}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-40"
          >
            {loading ? "Checking sources…" : "Ask"}
          </button>
        </div>
      </form>

      {error ? (
        <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {answer?.insufficient ? (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5">
          <p className="text-sm font-medium text-amber-200">
            Not enough evidence in the indexed documents.
          </p>
          <p className="mt-1 text-xs text-amber-200/70">
            {answer.rejected} claim(s) were dropped because their quotes could not
            be found in the cited source.
          </p>
        </div>
      ) : null}

      {answer && !answer.insufficient ? (
        <ul className="space-y-4">
          {answer.claims.map((claim, index) => (
            <li
              key={index}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <p className="text-sm leading-6 text-slate-100">{claim.text}</p>
              <ul className="mt-3 space-y-2">
                {claim.citations.map((citation, citationIndex) => (
                  <li
                    key={citationIndex}
                    className="rounded-lg bg-slate-950/70 p-3 text-xs leading-5 text-slate-400"
                  >
                    <span className="text-slate-500">{citation.label}</span>
                    <p className="mt-1 text-slate-300">&ldquo;{citation.quote}&rdquo;</p>
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
