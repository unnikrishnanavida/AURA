/**
 * Audit: security events recorded by the canonical audit log.
 */

import { useEffect, useState } from "react";
import { useSettings } from "../lib/settings-context";
import type { AuditRecord } from "../lib/types";

export function AuditPage() {
  const { api } = useSettings();
  const [records, setRecords] = useState<AuditRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .audit()
      .then(({ entries }) => {
        if (!cancelled) {
          setRecords(entries);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api]);

  return (
    <section aria-label="Audit log" className="panel">
      <h2>Audit log</h2>
      {busy ? <p>Loading…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {records ? (
        <table>
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
            {records.map((r) => (
              <tr key={`${r.timestamp}-${r.correlation_id ?? r.action}`}>
                <td>{r.timestamp}</td>
                <td>{r.actor}</td>
                <td>{r.action}</td>
                <td>{r.decision}</td>
                <td>{r.reason}</td>
              </tr>
            ))}
            {records.length === 0 ? (
              <tr>
                <td colSpan={5}>No audit events recorded yet.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}