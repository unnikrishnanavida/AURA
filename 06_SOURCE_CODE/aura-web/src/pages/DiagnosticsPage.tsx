/**
 * Diagnostics (advanced) — a human-first system status surface.
 * Normal users see a single friendly readiness line; raw health/readiness
 * details, system counters and telemetry stay tucked behind disclosure
 * controls. Progressive disclosure, no data invented.
 */

import { useEffect, useState } from "react";
import { useSettings } from "../lib/settings-context";
import { ApiError } from "../lib/api";
import { fetchOverview, type OverviewData } from "../lib/overview";
import type { HealthResult, MetricSnapshot, ReadyResult } from "../lib/types";

interface StatusState {
  health: HealthResult | null;
  ready: ReadyResult | null;
  metrics: MetricSnapshot | null;
  error: string | null;
  loading: boolean;
}

function chipTone(status: string | null): string {
  const s = (status ?? "").toLowerCase();
  if (s === "ok" || s === "ready" || s === "active" || s === "healthy" || s === "up") return "ok";
  if (s.includes("degrad") || s.includes("warn") || s.includes("partial") || s === "not_ready") return "warn";
  return "error";
}

function describeError(reason: unknown): string {
  if (reason instanceof ApiError) {
    return `AURA API ${reason.status}: ${reason.code} — ${reason.message}`;
  }
  return "Could not reach the AURA connection.";
}

export function DiagnosticsPage() {
  const { api, endpoint, apiKey } = useSettings();
  const [state, setState] = useState<StatusState>({ health: null, ready: null, metrics: null, error: null, loading: true });
  const [overview, setOverview] = useState<OverviewData | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([api.health(), api.ready(), api.metrics()]).then(([h, r, m]) => {
      if (cancelled) return;
      setState({
        health: h.status === "fulfilled" ? h.value : null,
        ready: r.status === "fulfilled" ? r.value : null,
        metrics: m.status === "fulfilled" ? m.value : null,
        error:
          h.status === "rejected"
            ? describeError(h.reason)
            : m.status === "rejected"
              ? describeError(m.reason)
              : null,
        loading: false,
      });
    });
    void fetchOverview(endpoint, apiKey)
      .then((data) => {
        if (!cancelled) setOverview(data);
      })
      .catch(() => {
        if (!cancelled) setOverview(null);
      });
    return () => {
      cancelled = true;
    };
  }, [api, endpoint, apiKey]);

  const readyStatus = (state.ready?.status ?? "").toLowerCase();
  const allOk =
    state.health?.status === "ok" &&
    (readyStatus === "ok" || readyStatus === "ready") &&
    !state.error;

  return (
    <section aria-label="Diagnostics" className="panel">
      <h2>Diagnostics</h2>
      {state.loading ? <p className="hint">Checking AURA…</p> : null}
      {state.error ? <p className="error" role="alert">{state.error}</p> : null}
      {!state.error && (state.health || state.ready) ? (
        <div className="ready-card" aria-live="polite">
          <span className="status-pill-dot" aria-hidden="true" />
          <strong>{allOk ? "AURA is ready." : "AURA is available, with attention needed."}</strong>
          <span className="hint">System diagnostics are shown below for advanced users.</span>
        </div>
      ) : null}
      {state.health || state.ready ? (
        <details className="diag-block" open={!allOk}>
          <summary>Service status</summary>
          <div className="status-chips">
            {state.health ? (
              <span className={`status-chip ${chipTone(state.health.status)}`} aria-label="API health">
                API · {state.health.status}
              </span>
            ) : null}
            {state.ready ? (
              <span className={`status-chip ${chipTone(state.ready.status)}`} aria-label="Readiness">
                Ready · {state.ready.status}
              </span>
            ) : null}
          </div>
        </details>
      ) : null}
      {overview ? (
        <details className="diag-block">
          <summary>System overview</summary>
          <div className="stats-inline">
            <span><b>{overview.executionCount}</b> reasoning sessions</span>
            <span><b>{overview.knowledgeCount}</b> knowledge claims</span>
            <span><b>{overview.memoryCount}</b> memory entries</span>
            <span><b>{overview.rateLimitDenials}</b> rate-limit denials</span>
          </div>
        </details>
      ) : null}
      {state.metrics ? (
        <details className="diag-block">
          <summary>Live telemetry</summary>
          <pre>{JSON.stringify(state.metrics, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}