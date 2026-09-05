/**
 * Memory inspection: write and recall records through the AURA API.
 */

import { useState, type FormEvent } from "react";
import { useSettings } from "../lib/settings-context";
import type { MemoryEntry } from "../lib/types";

export function MemoryPage() {
  const { api } = useSettings();
  const [key, setKey] = useState("");
  const [content, setContent] = useState("{}");
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<MemoryEntry[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onRemember(e: FormEvent) {
    e.preventDefault();
    if (!key.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const parsed = JSON.parse(content || "{}") as Record<string, unknown>;
      const { memory_id } = await api.remember(key, parsed);
      setMessage(`remembered as ${memory_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onRecall(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { entries: found } = await api.recall(query, 10);
      setEntries(found);
      setMessage(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Memory" className="panel">
      <h2>Memory</h2>
      <form onSubmit={onRemember} aria-label="Remember">
        <label>
          Key
          <input value={key} onChange={(e) => setKey(e.target.value)} placeholder="deployment-state" required />
        </label>
        <label>
          Content (JSON)
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
            placeholder='{"phase": "canary"}'
          />
        </label>
        <button type="submit" disabled={busy || !key.trim()}>
          Remember
        </button>
      </form>
      <form onSubmit={onRecall} aria-label="Recall" className="row">
        <label>
          Query
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="deployment" />
        </label>
        <button type="submit" disabled={busy}>
          Recall
        </button>
      </form>
      {message ? <p className="ok">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {entries ? (
        <div>
          <h3>Results ({entries.length})</h3>
          <ul>
            {entries.map((entry) => (
              <li key={entry.id}>
                <strong>{entry.key}</strong> ({entry.kind}) —{" "}
                <code>{JSON.stringify(entry.content)}</code>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}