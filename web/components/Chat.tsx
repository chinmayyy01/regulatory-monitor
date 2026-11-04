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
      if (!response.ok) throw new Error("We couldn’t answer right now. Please try again in a moment.");
      setAnswer((await response.json()) as AskResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We couldn’t connect. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="workspace-chat space-y-6">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit(question);
        }}
        className="workspace-panel space-y-4 p-4 sm:p-5"
      >
        <label htmlFor="regulation-question" className="block font-medium">Your question</label>
        <textarea
          id="regulation-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={4}
          maxLength={1000}
          aria-describedby="question-help question-count"
          placeholder="For example: How quickly must we resolve customer complaints?"
          className="workspace-input min-h-28 w-full resize-y p-3 text-base leading-6"
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p id="question-help" className="text-sm leading-5 text-[var(--ws-muted)]">
            Answers use the indexed regulations and this workspace’s policies. Unsupported answers are withheld.
          </p>
          <p id="question-count" className="text-sm tabular-nums text-[var(--ws-muted)]">{question.length}/1,000</p>
        </div>
        <div className="workspace-chat-actions border-t border-[var(--ws-border)] pt-4">
          <div className="min-w-0">
            <p className="mb-2 text-sm font-medium">Need a starting point? Choose a question</p>
            <div className="workspace-suggestions">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setQuestion(suggestion);
                  setAnswer(null);
                  setError(null);
                }}
                className="workspace-suggestion min-h-11 px-3 py-2 text-left text-sm"
              >
                {suggestion}
              </button>
            ))}
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || question.trim().length < 3}
            className="workspace-button workspace-button-primary workspace-chat-submit min-h-11 px-5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Checking sources…" : "Get an answer"}
          </button>
        </div>
      </form>

      {error ? (
        <p role="alert" className="workspace-error p-4 text-sm leading-5">
          {error}
        </p>
      ) : null}

      {answer?.insufficient ? (
        <section role="status" className="workspace-empty-state" aria-labelledby="no-evidence-title">
          <h2 id="no-evidence-title" className="font-semibold">There isn’t enough evidence to answer</h2>
          <p className="mt-2 text-sm leading-5 text-[var(--ws-muted)]">
            No answer passed the source checks. Try asking about a specific requirement or add the policy document that may contain it.
          </p>
          {answer.rejected + answer.unsupported > 0 ? <p className="mt-3 text-sm text-[var(--ws-muted)]">{answer.rejected + answer.unsupported} unsupported claim{answer.rejected + answer.unsupported === 1 ? "" : "s"} withheld.</p> : null}
        </section>
      ) : null}

      {answer && !answer.insufficient ? (
        <section aria-live="polite" aria-label="Answer and sources">
          <h2 className="mb-3 text-lg font-semibold">Answer</h2>
          <ul className="space-y-4">
          {answer.claims.map((claim, index) => (
            <li key={index} className="workspace-panel p-4 sm:p-5">
              <p className="text-base leading-6">{claim.text}</p>
              <ul className="mt-4 space-y-3" aria-label="Supporting sources">
                {claim.citations.map((citation, citationIndex) => (
                  <li key={citationIndex} className="workspace-evidence-block">
                    <p className="font-medium">{citation.kind === "regulation" ? "Regulatory source" : "Workspace policy"}</p>
                    <p className="mt-1 text-sm text-[var(--ws-muted)]">{citation.label}</p>
                    <blockquote className="mt-2 text-sm leading-5 text-[var(--ws-text-secondary)]">“{citation.quote}”</blockquote>
                  </li>
                ))}
              </ul>
            </li>
          ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
