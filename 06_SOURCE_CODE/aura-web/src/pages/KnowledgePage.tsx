/**
 * Knowledge: add claims and retrieve claims through the AURA API.
 * Explanation-first copy; every value still comes live from the API.
 */

import { useState, type FormEvent } from "react";
import { useSettings } from "../lib/settings-context";
import type { ClaimEntry } from "../lib/types";

export function KnowledgePage() {
  const { api } = useSettings();
  const [statement, setStatement] = useState("");
  const [query, setQuery] = useState("");
  const [claims, setClaims] = useState<ClaimEntry[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onObserve(e: FormEvent) {
    e.preventDefault();
    if (!statement.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const { claim_id } = await api.observe(statement);
      setMessage(`Saved as a knowledge claim (${claim_id}).`);
      setStatement("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onRetrieve(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { claims: found } = await api.retrieve(query, 10);
      setClaims(found);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Knowledge" className="panel">
      <h2>Knowledge</h2>
      <p className="hint knowledge-intro">
        Knowledge is a store of factual claims about your world. Teach AURA a statement, or retrieve what it already
        knows.
      </p>
      <form onSubmit={onObserve} aria-label="Observe">
        <label>
          What do you want AURA to know?
          <input value={statement} onChange={(e) => setStatement(e.target.value)} placeholder="deployment requires approval" required />
        </label>
        <button type="submit" disabled={busy || !statement.trim()}>
          Save claim
        </button>
      </form>
      <form onSubmit={onRetrieve} aria-label="Retrieve" className="row">
        <label>
          Ask AURA what it knows
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="deployment" />
        </label>
        <button type="submit" disabled={busy}>
          Recall
        </button>
      </form>
      {message ? <p className="ok">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {claims ? (
        <ul className="list">
          {claims.map((claim) => (
            <li key={claim.claim_id}>
              <strong>{claim.statement}</strong> — status {claim.status}, confidence {claim.confidence.toFixed(3)}
            </li>
          ))}
          {claims.length === 0 ? <li>No claims matched.</li> : null}
        </ul>
      ) : null}
    </section>
  );
}