/**
 * ChatComposer — the primary AURA interaction surface.
 * Multiline, Enter to send, Shift+Enter for a newline, disabled while
 * reasoning, stop-generation affordance, keyboard accessible, gold focus.
 */

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
  onStop?: () => void;
  placeholder?: string;
  autoFocus?: boolean;
  hint?: string;
  id: string;
}

export function ChatComposer({
  value,
  onChange,
  onSubmit,
  busy,
  onStop,
  placeholder = "Ask AURA anything…",
  autoFocus = true,
  id,
}: ChatComposerProps) {
  const ref = useRef<HTMLTextAreaElement | null>(null);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 190)}px`;
  }, [value]);

  useEffect(() => {
    if (autoFocus) ref.current?.focus();
  }, [autoFocus]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!busy && value.trim()) onSubmit();
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    (document.activeElement as HTMLElement | null)?.blur();
    window.setTimeout(() => ref.current?.focus(), 0);
    onSubmit();
  }

  const canSend = value.trim() !== "" && !busy;

  return (
    <form className="composer-form" onSubmit={submit} aria-busy={busy}>
      <div className={`composer ${busy ? "is-busy" : ""} ${dirty ? "is-dirty" : ""}`}>
        <label className="sr-only" htmlFor={id}>
          Ask AURA anything
        </label>
        <textarea
          id={id}
          ref={ref}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            if (e.target.value !== "") setDirty(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={busy}
          rows={1}
          autoComplete="off"
          aria-label="Ask AURA anything"
        />
        {busy ? (
          <button
            type="button"
            className="composer-send is-stop"
            aria-label="Stop generating"
            title="Stop generating"
            onClick={onStop}
          >
            <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
              <rect x="3" y="3" width="10" height="10" rx="2" fill="currentColor" />
            </svg>
          </button>
        ) : (
          <button
            type="submit"
            className="composer-send"
            aria-label="Send message"
            title="Send message (Enter)"
            disabled={!canSend}
          >
            <svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 19V5" />
              <path d="M5 12l7-7 7 7" />
            </svg>
          </button>
        )}
      </div>
    </form>
  );
}