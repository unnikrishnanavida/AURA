/**
 * Reasoning console: ask the AURA API a question and show the structured answer.
 */

import { useState, type FormEvent } from "react";
import { useSettings } from "../lib/settings-context";
import type { ReasonResult } from "../lib/types";

export function ConsolePage() {
  const { api } = useSettings();
  const [question, setQuestion] = useState("");
  const [fact, setFact] = useState("");
  const [result, setResult] = useState<ReasonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const facts: Record<string, number> = {};
      const trimmed = fact.trim();
      if (trimmed) facts[trimmed] = 0.9;
      setResult(await api.reason(question, facts));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Reasoning console" className="panel">
      <h2>Reasoning console</h2>
      <form onSubmit={onSubmit}>
        <label>
          Question
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. is the deployment safe?"
            required
          />
        </label>
        <label>
          Supporting fact (optional)
          <input value={fact} onChange={(e) => setFact(e.target.value)} placeholder="e.g. tests_passed" />
        </label>
        <button type="submit" disabled={busy || !question.trim()}>
          {busy ? "Reasoning…" : "Reason"}
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      {result ? (
        <dl>
          <dt>Answer</dt>
          <dd>{result.answer ?? "(no answer)"}</dd>
          <dt>Confidence</dt>
          <dd>{result.confidence ?? "—"}</dd>
          <dt>Uncertainty</dt>
          <dd>{result.uncertainty ?? "—"}</dd>
          <dt>Execution id</dt>
          <dd>{result.execution_id}</dd>
        </dl>
      ) : null}
    </section>
  );
}