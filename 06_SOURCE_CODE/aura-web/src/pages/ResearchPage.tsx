/**
 * Research: run an evidence-aware research cycle through the AURA API.
 */

import { useState, type FormEvent } from "react";
import { useSettings } from "../lib/settings-context";
import type { ResearchOutput } from "../lib/types";

export function ResearchPage() {
  const { api } = useSettings();
  const [question, setQuestion] = useState("");
  const [claim, setClaim] = useState("");
  const [claims, setClaims] = useState<string[]>([]);
  const [output, setOutput] = useState<ResearchOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function addClaim(e: FormEvent) {
    e.preventDefault();
    const trimmed = claim.trim();
    if (trimmed && !claims.includes(trimmed)) {
      setClaims([...claims, trimmed]);
    }
    setClaim("");
  }

  async function onRun(e: FormEvent) {
    e.preventDefault();
    if (!question.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      setOutput(await api.research(question, claims));
    } catch (err) {
      setOutput(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Research" className="panel">
      <h2>Research</h2>
      <form onSubmit={onRun}>
        <label>
          Question
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What is the best approach?" required />
        </label>
        <div className="row">
          <input value={claim} onChange={(e) => setClaim(e.target.value)} placeholder="Add a claim to assess…" />
          <button type="button" className="ghost" onClick={addClaim}>
            Add claim
          </button>
        </div>
        {claims.length ? (
          <ul className="tags">
            {claims.map((c) => (
              <li key={c}>
                {c}{" "}
                <button type="button" aria-label={`remove ${c}`} onClick={() => setClaims(claims.filter((x) => x !== c))}>
                  ×
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        <button type="submit" disabled={busy || !question.trim()}>
          {busy ? "Researching…" : "Run research"}
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      {output ? (
        <div>
          <h3>Research output</h3>
          <p>
            Epistemic: {output.epistemic} · overall confidence {output.overall_confidence.toFixed(3)}
          </p>
          <p>Synthesis: {output.synthesis}</p>
          {output.contradictions.length ? (
            <p className="error">Contradictions: {output.contradictions.length}</p>
          ) : null}
          <h4>Findings</h4>
          <ul className="list">
            {output.findings.map((f) => (
              <li key={f.claim}>
                <strong>{f.claim}</strong> — {f.status} (conf {f.confidence.toFixed(3)})
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}