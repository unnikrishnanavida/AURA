/**
 * Research: run an evidence-aware research cycle through the AURA API and
 * browse the caller's real research runs (GET /v1/research/runs).
 */

import dayjs from "dayjs";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ArrowRight, FlaskConical, Plus, RotateCcw, X } from "lucide-react";
import { useSettings } from "../lib/settings-context";
import type { ResearchOutput, ResearchRun } from "../lib/types";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  const parsed = dayjs(value);
  return parsed.isValid() ? parsed.format("YYYY-MM-DD HH:mm") : value;
}

export function ResearchPage() {
  const { api } = useSettings();
  const [question, setQuestion] = useState("");
  const [claim, setClaim] = useState("");
  const [claims, setClaims] = useState<string[]>([]);
  const [output, setOutput] = useState<ResearchOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [runsLoading, setRunsLoading] = useState(true);
  const [runsError, setRunsError] = useState<string | null>(null);

  const refreshRuns = useCallback(
    async (cursor?: number) => {
      try {
        setRunsError(null);
        if (cursor === undefined) setRunsLoading(true);
        const page = await api.listResearchRuns(20, cursor);
        setRuns((previous) => (cursor === undefined ? page.runs : [...previous, ...page.runs]));
        setNextCursor(page.next_cursor);
      } catch (err) {
        setRunsError(err instanceof Error ? err.message : String(err));
      } finally {
        setRunsLoading(false);
      }
    },
    [api],
  );

  useEffect(() => {
    let cancelled = false;
    api
      .listResearchRuns(20)
      .then((page) => {
        if (cancelled) return;
        setRuns(page.runs);
        setNextCursor(page.next_cursor);
        setRunsError(null);
      })
      .catch((err) => {
        if (!cancelled) setRunsError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setRunsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api]);

  function addClaimFromButton() {
    const trimmed = claim.trim();
    if (trimmed && !claims.includes(trimmed)) setClaims([...claims, trimmed]);
    setClaim("");
  }

  async function onRun(e: FormEvent) {
    e.preventDefault();
    if (!question.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      setOutput(await api.research(question, claims));
      void refreshRuns();
    } catch (err) {
      setOutput(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Research" className="research-workspace">
      <header className="research-heading">
        <div>
          <p className="research-eyebrow">AURA / RESEARCH</p>
          <h2>Research engine</h2>
          <p>Explore a question through AURA’s evidence-aware research pipeline.</p>
        </div>
        <FlaskConical aria-hidden="true" className="research-heading-icon" />
      </header>

      <div className="research-grid">
        <div className="panel rw-main research-compose">
          <div className="research-panel-heading">
            <span className="research-kicker">NEW INQUIRY</span>
            <h3>What would you like to understand?</h3>
          </div>
          <form className="research-form" onSubmit={onRun} aria-busy={busy}>
            <label htmlFor="research-question">Research question</label>
            <textarea
              id="research-question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Write a question to investigate…"
              required
              rows={4}
            />
            <details className="research-claim-options">
              <summary><Plus aria-hidden="true" /> Add claims to assess <span>Optional</span></summary>
              <div className="research-claim-row">
                <label className="sr-only" htmlFor="research-claim">Claim to assess</label>
                <input
                  id="research-claim"
                  value={claim}
                  onChange={(e) => setClaim(e.target.value)}
                  placeholder="Enter a claim…"
                />
                <button type="button" className="ghost" onClick={addClaimFromButton} disabled={!claim.trim()}>
                  Add claim
                </button>
              </div>
              {claims.length ? (
                <ul className="research-claims-list" aria-label="Claims to assess">
                  {claims.map((item) => (
                    <li key={item}>
                      <span>{item}</span>
                      <button
                        type="button"
                        className="research-remove-claim"
                        aria-label={`Remove claim: ${item}`}
                        onClick={() => setClaims(claims.filter((candidate) => candidate !== item))}
                      >
                        <X aria-hidden="true" />
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </details>
            <div className="research-form-footer">
              <p className="hint" aria-live="polite">
                {busy ? "AURA is researching…" : "Results come from the connected AURA research pipeline."}
              </p>
              <button type="submit" className="research-submit" disabled={busy || !question.trim()}>
                {busy ? <FlaskConical aria-hidden="true" /> : <ArrowRight aria-hidden="true" />}
                {busy ? "Researching…" : "Run research"}
              </button>
            </div>
          </form>
          {error ? <p className="error research-error" role="alert">{error}</p> : null}
        </div>

        <aside className="panel rw-side" aria-label="Research run history">
          <div className="research-history-heading">
            <div>
              <span className="research-kicker">YOUR WORKSPACE</span>
              <h3>Recent research</h3>
            </div>
            {runs.length ? <span className="research-run-count">{runs.length}</span> : null}
          </div>
          {runsLoading ? <p className="hint" aria-live="polite" aria-busy="true">Loading recent runs…</p> : null}
          {runsError ? <p className="error" role="alert">Could not load recent runs: {runsError}</p> : null}
          {runsError ? (
            <button type="button" className="ghost research-retry" onClick={() => void refreshRuns()}>
              <RotateCcw aria-hidden="true" /> Retry loading runs
            </button>
          ) : null}
          {!runsLoading && !runsError && runs.length === 0 ? (
            <div className="research-history-empty">
              <p>No research runs recorded yet.</p>
              <span>Runs you create will appear here.</span>
            </div>
          ) : null}
          {runs.length > 0 ? (
            <ul className="list runs" aria-label="Research runs">
              {runs.map((run) => (
                <li key={run.run_id}>
                  <div className="run-row">
                    <div>
                      <strong>{run.question || "Untitled research run"}</strong>
                      <span className="hint">
                        {formatTimestamp(run.started_at)}
                        {run.findings_count !== null ? ` · ${run.findings_count} finding(s)` : ""}
                      </span>
                    </div>
                    <span className="status-badge">
                      {run.status}
                      {run.epistemic ? ` · ${run.epistemic}` : ""}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
          {nextCursor !== null && !runsLoading ? (
            <button type="button" className="ghost research-retry" onClick={() => void refreshRuns(nextCursor)}>
              Load older runs
            </button>
          ) : null}
        </aside>
      </div>

      {output ? (
        <section className="panel research-output" aria-label="Research results" aria-live="polite">
          <div className="research-output-heading">
            <div>
              <span className="research-kicker">RESEARCH COMPLETE</span>
              <h3>Findings</h3>
            </div>
            <span className="status-badge">{output.epistemic}</span>
          </div>
          <p className="research-synthesis">{output.synthesis}</p>
          <dl className="research-summary">
            <div><dt>Confidence</dt><dd>{output.overall_confidence.toFixed(2)}</dd></div>
            <div><dt>Findings</dt><dd>{output.findings.length}</dd></div>
            <div><dt>Contradictions</dt><dd>{output.contradictions.length}</dd></div>
          </dl>
          {output.findings.length ? (
            <ul className="research-findings">
              {output.findings.map((finding, index) => (
                <li key={`${finding.claim}-${index}`}>
                  <div className="finding-heading">
                    <strong>{finding.claim}</strong>
                    <span className="status-badge">{finding.status}</span>
                  </div>
                  <p className="hint">
                    Confidence {finding.confidence.toFixed(2)} · {finding.evidence_count} evidence item(s)
                  </p>
                  {finding.supporting.length || finding.contradicting.length ? (
                    <details className="finding-evidence">
                      <summary>View evidence</summary>
                      {finding.supporting.length ? <p><strong>Supporting</strong> {finding.supporting.join(" · ")}</p> : null}
                      {finding.contradicting.length ? <p><strong>Contradicting</strong> {finding.contradicting.join(" · ")}</p> : null}
                    </details>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
          {output.contradictions.length ? (
            <details className="research-contradictions">
              <summary>Review contradictions ({output.contradictions.length})</summary>
              <ul>
                {output.contradictions.map((pair, index) => <li key={index}>{pair.join(" vs ")}</li>)}
              </ul>
            </details>
          ) : null}
        </section>
      ) : null}
    </section>
  );
}