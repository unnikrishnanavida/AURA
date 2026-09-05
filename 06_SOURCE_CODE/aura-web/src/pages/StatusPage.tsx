/**
 * System status: live health/readiness/metrics pulled from the AURA API.
 */

import { useEffect, useState } from "react";
import { useSettings } from "../lib/settings-context";
import { ApiError } from "../lib/api";
import type { HealthResult, MetricSnapshot, ReadyResult } from "../lib/types";

interface StatusState {
  health: HealthResult | null;
  ready: ReadyResult | null;
  metrics: MetricSnapshot | null;
  error: string | null;
  loading: boolean;
}

export function StatusPage() {
  const { api } = useSettings();
  const [state, setState] = useState<StatusState>({
    health: null,
    ready: null,
    metrics: null,
    error: null,
    loading: true,
  });

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
    return () => {
      cancelled = true;
    };
  }, [api]);

  return (
    <section aria-label="System status" className="panel">
      <h2>System status</h2>
      {state.loading ? <p>Checking…</p> : null}
      {state.error ? <p className="error">{state.error}</p> : null}
      {state.health ? <p>Health: {state.health.status}</p> : null}
      {state.ready ? <p>Ready: {state.ready.status}</p> : null}
      {state.metrics ? (
        <div>
          <h3>Metrics (live)</h3>
          <pre>{JSON.stringify(state.metrics, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

function describeError(reason: unknown): string {
  if (reason instanceof ApiError) {
    return `API ${reason.status}: ${reason.code} — ${reason.message}`;
  }
  return String(reason);
}