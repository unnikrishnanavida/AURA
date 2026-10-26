/**
 * Documents: the user's personal notes, stored in AURA's long-term memory.
 * Every value is live from the real notes API; nothing is fabricated.
 * Advanced scope handling is tucked behind a disclosure control.
 */

import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/aura/EmptyState";
import { FileText } from "lucide-react";
import { NotesClient, type Note } from "../lib/notes";
import { useSettings } from "../lib/settings-context";

export function DocumentsPage() {
  const { endpoint, apiKey } = useSettings();
  const [scope, setScope] = useState("owner:anonymous");
  const client = useMemo(() => new NotesClient(endpoint, apiKey, scope), [endpoint, apiKey, scope]);
  const [notes, setNotes] = useState<Note[] | null>(null);
  const [selected, setSelected] = useState<Note | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const refresh = useCallback(() => {
    void client
      .list()
      .then((items) => setNotes(items))
      .catch((err) => {
        setError(err instanceof Error ? err.message : String(err));
        setNotes([]);
      });
  }, [client]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (selected) {
      await saveSelected();
    } else {
      await createNote(e);
    }
  }

  async function createNote(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await client.create({ title, content });
      setTitle("");
      setContent("");
      setNotice("Saved.");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function saveSelected() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await client.update(selected.note_id, { title, content });
      setNotice("Updated.");
      setSelected(updated);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function deleteSelected() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const removed = await client.remove(selected.note_id);
      setNotice(removed ? "Deleted." : "Delete failed");
      setSelected(null);
      setConfirmDelete(false);
      setTitle("");
      setContent("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function open(note: Note) {
    setSelected(note);
    setConfirmDelete(false);
    setTitle(note.title);
    setContent(note.content);
  }

  return (
    <section aria-label="Documents and notes" className="panel">
      <h2>Documents</h2>
      <p className="hint documents-intro">
        Your personal notes live in AURA&rsquo;s memory and stay private to you. Write a draft, open a saved note, or update it
        anytime.
      </p>
      <form onSubmit={(e) => void onSubmit(e)} aria-busy={busy}>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} placeholder="e.g. Deployment runbook" />
        </label>
        <label>
          Content
          <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={6} placeholder="Write what you need to remember…" />
        </label>
        <button type="submit" disabled={busy || title.trim() === ""}>
          {selected ? "Update note" : "Save note"}
        </button>
        {selected && !confirmDelete ? (
          <button type="button" className="ghost" disabled={busy} onClick={() => setConfirmDelete(true)}>
            Delete note
          </button>
        ) : null}
        {selected && confirmDelete ? (
          <div className="note-delete-confirm" role="alertdialog" aria-labelledby="note-delete-title" aria-describedby="note-delete-description">
            <p id="note-delete-title">Delete “{selected.title}”?</p>
            <p id="note-delete-description" className="hint">This note will be removed from AURA’s memory.</p>
            <div className="actions">
              <button type="button" className="ghost" disabled={busy} onClick={() => setConfirmDelete(false)}>
                Cancel
              </button>
              <button type="button" className="note-delete-action" disabled={busy} onClick={() => void deleteSelected()}>
                Confirm delete
              </button>
            </div>
          </div>
        ) : null}
      </form>
      <details className="doc-scope">
        <summary>Note scope (advanced)</summary>
        <label>
          Scope
          <input value={scope} onChange={(e) => setScope(e.target.value)} aria-label="Note scope" />
        </label>
        <p className="hint">Notes are isolated per scope on the server. The default keeps them private to you.</p>
      </details>
      {notice ? <p className="hint" role="status">{notice}</p> : null}
      {error ? <p className="error" role="alert">{error}</p> : null}
      <div role="list" aria-label="Saved notes">
        {notes === null ? <p className="hint">Loading your notes…</p> : null}
        {notes !== null && notes.length === 0 ? (
          <EmptyState
            icon={<FileText aria-hidden="true" />}
            title="No notes yet"
            body="Notes you save appear here and are kept private to you in AURA's memory."
          />
        ) : null}
        {(notes ?? []).map((note) => (
          <article key={note.note_id} role="listitem" className="note-card">
            <button type="button" className="ghost" onClick={() => open(note)}>
              {note.title}
            </button>
            <p className="hint">{note.content.slice(0, 120)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}