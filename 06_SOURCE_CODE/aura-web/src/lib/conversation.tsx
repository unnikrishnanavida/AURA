/**
 * Conversation: user question history with structured assistant answers,
 * loading state with cancel, per-turn retry, and safe provider metadata.
 * No hidden chain-of-thought is rendered — only the structured answer,
 * confidence/uncertainty, and (Phase 29) the synthesizing provider name.
 */

import { useState, type FormEvent } from "react";
import { ApiError } from "./api";
import { useSettings } from "./settings-context";
import type { ReasonResult } from "./types";

interface Turn {
  question: string;
  answer?: string;
  confidence?: number | null;
  uncertainty?: string | null;
  provider?: string | null;
  status: "ok" | "error" | "cancelled";
  message?: string;
}

export function Conversation() {
  const { api } = useSettings();
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [controller, setController] = useState<AbortController | null>(null);

  function run(turnIndex: number, text: string) {
    if (controller) controller.abort();
    const current = new AbortController();
    setController(current);
    setBusy(true);
    setTurns((previous) => {
      const next = [...previous];
      next[turnIndex] = { question: text, status: "ok" };
      return next;
    });
    void api
      .reason(text, {}, current.signal)
      .then((result: ReasonResult) => {
        setTurns((previous) => {
          const next = [...previous];
          next[turnIndex] = {
            question: text,
            answer: result.answer ?? "(no answer)",
            confidence: result.confidence,
            uncertainty: result.uncertainty,
            provider: result.provider?.name,
            status: "ok",
          };
          return next;
        });
      })
      .catch((err: unknown) => {
        const cancelled = err instanceof ApiError && err.code === "sdk.cancelled";
        setTurns((previous) => {
          const next = [...previous];
          next[turnIndex] = {
            question: text,
            status: cancelled ? "cancelled" : "error",
            message: cancelled ? "cancelled" : err instanceof Error ? err.message : String(err),
          };
          return next;
        });
      })
      .finally(() => {
        setBusy(false);
        setController(null);
      });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setQuestion("");
    const turnIndex = turns.length;
    setTurns([...turns, { question: text, status: "ok" }]);
    run(turnIndex, text);
  }

  function retry(turnIndex: number) {
    const questionText = turns[turnIndex]?.question ?? "";
    if (questionText && !busy) run(turnIndex, questionText);
  }

  function cancel() {
    if (controller) controller.abort();
  }

  return (
    <section aria-label="Reasoning console" className="panel">
      <h2>Reasoning console</h2>
      <form onSubmit={onSubmit} aria-busy={busy}>
        <label>
          Question
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. is the deployment safe?"
            disabled={busy}
          />
        </label>
        <div className="actions">
          <button type="submit" disabled={busy || !question.trim()}>
            {busy ? "Reasoning…" : "Reason"}
          </button>
          {busy ? (
            <button type="button" className="ghost" onClick={cancel}>
              Cancel
            </button>
          ) : null}
        </div>
      </form>
      <div role="list" aria-live="polite" className="turns">
        {turns.map((turn, index) => (
          <article key={`${index}-${turn.question}`} role="listitem" className="turn">
            <p className="question">{turn.question}</p>
            {turn.status === "ok" ? (
              <dl>
                <dt>Answer</dt>
                <dd>{turn.answer ?? "…"}</dd>
                {turn.confidence !== undefined ? (
                  <>
                    <dt>Confidence</dt>
                    <dd>{turn.confidence}</dd>
                  </>
                ) : null}
                {turn.uncertainty ? (
                  <>
                    <dt>Uncertainty</dt>
                    <dd>{turn.uncertainty}</dd>
                  </>
                ) : null}
                {turn.provider ? (
                  <>
                    <dt>Synthesized by</dt>
                    <dd>{turn.provider}</dd>
                  </>
                ) : null}
              </dl>
            ) : turn.status === "cancelled" ? (
              <p className="hint">Cancelled.</p>
            ) : (
              <p className="error" role="alert">
                {turn.message}
                <button type="button" className="ghost" onClick={() => retry(index)} disabled={busy}>
                  Retry
                </button>
              </p>
            )}
          </article>
        ))}
        {turns.length === 0 ? <p className="hint">Ask a question to start.</p> : null}
      </div>
    </section>
  );
}