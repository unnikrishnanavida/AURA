/**
 * Security Log (advanced) — an explicit, user-requested copy of the security
 * log for support/debugging. The log is served live from the canonical AURA
 * audit log via POST /v1/security/logs and the request itself is recorded as
 * a security event. Nothing is ever stored in the browser.
 */

import { useState } from "react";
import { EmptyState } from "../components/aura/EmptyState";
import { ShieldCheck } from "lucide-react";
import { useSettings } from "../lib/settings-context";
import type { SecurityLogEntry } from "../lib/types";

function decisionTone(decision: string): "ok" | "no" | "warn" {
  const d = decision.toLowerCase();
  if (d.includes("allow") || d.includes("accept") || d.includes("approv") || d.includes("ok")) return "ok";
  if (d.includes("deny") || d.includes("reject") || d.includes("block")) return "no";
  return "warn";
}

export function SecurityLogPage() {
  const { api } = useSettings();
  const [entries, setEntries] = useState<SecurityLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");

  async function onRequest() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { entries: found } = await api.securityLogs(reason);
      setEntries(found);
      setReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Security Log" className="panel">
      <h2>Security Log</h2>
      <div className="security-log-intro">
        <p className="hint">
          Export a copy of the security log to share with support or keep for your records. The log is requested live
          from the AURA API — this browser never stores it.
        </p>
        <form
          className="security-log-request"
          onSubmit={(e) => {
            e.preventDefault();
            void onRequest();
          }}
        >
          <label className="sr-only" htmlFor="security-log-reason">
            Reason
          </label>
          <input
            id="security-log-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            maxLength={240}
            placeholder="Why do you need it? (optional)"
          />
          <button type="submit" disabled={busy} className="ghost">
            <ShieldCheck aria-hidden="true" />
            {busy ? "Requesting…" : "Request security log"}
          </button>
        </form>
      </div>
      {error ? <p className="error" role="alert">{error}</p> : null}
      {entries !== null && entries.length === 0 ? (
        <EmptyState
          icon={<ShieldCheck aria-hidden="true" />}
          title="No security events yet"
          body="The server has not recorded any security events. They will appear here as AURA works and decides."
        />
      ) : null}
      {entries && entries.length > 0 ? (
        <table className="security-log-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Decision</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((r) => (
              <tr key={`${r.timestamp}-${r.correlation_id ?? r.action}`}>
                <td className="mono-cell">{r.timestamp}</td>
                <td>{r.actor}</td>
                <td>{r.action}</td>
                <td>
                  <span className={`dec-badge ${decisionTone(r.decision)}`}>{r.decision}</span>
                </td>
                <td>{r.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {entries === null && !error ? (
        <EmptyState
          icon={<ShieldCheck aria-hidden="true" />}
          title="Security log is kept private"
          body="Press “Request security log” above to fetch a live copy from the AURA API."
        />
      ) : null}
    </section>
  );
}