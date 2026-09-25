/**
 * Authentication gate: shows a sign-in panel with credential error handling and
 * session state until the configured endpoint accepts the supplied API key.
 * The key is kept in session storage only (see settings provider).
 */

import { useState, type FormEvent, type ReactNode } from "react";
import { AuraApi, ApiError } from "./api";
import { useSettings } from "./settings-context";

export function AuthGate({ children }: { children: ReactNode }) {
  const { endpoint, apiKey, update, clearCredentials } = useSettings();
  const [signedIn, setSignedIn] = useState(apiKey !== "");
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextKey, setNextKey] = useState(apiKey);

  if (signedIn) {
    return (
      <div className="auth-session" data-testid="auth-session">
        <span>
          Signed in · <span className="endpoint">{endpoint}</span>
        </span>
        <button
          type="button"
          className="ghost"
          onClick={() => {
            clearCredentials();
            setSignedIn(false);
            setNextKey("");
            setError(null);
          }}
        >
          Sign out
        </button>
        {children}
      </div>
    );
  }

  async function onSignIn(e: FormEvent) {
    e.preventDefault();
    const trimmed = nextKey.trim();
    if (trimmed === "") return;
    setVerifying(true);
    setError(null);
    update({ apiKey: trimmed });
    try {
      const config = { apiKey: trimmed, endpoint };
      await verifyConnection(config.apiKey, config.endpoint);
      setSignedIn(true);
    } catch (err) {
      clearCredentials();
      if (err instanceof ApiError && err.status === 401) {
        setError("The API key was rejected (401). Check the key and try again.");
      } else {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      setVerifying(false);
    }
  }

  return (
    <section aria-label="Sign in" className="panel signin">
      <h2>Sign in to AURA</h2>
      <form onSubmit={onSignIn}>
        <label>
          API key
          <input
          type="password"
          value={nextKey}
          onChange={(e) => setNextKey(e.target.value)}
          autoComplete="off"
          required
          placeholder="Bearer token issued by the AURA API"
        />
        </label>
        <p className="hint">
          Endpoint: <span className="endpoint">{endpoint}</span>
        </p>
        <div className="actions">
          <button type="submit" disabled={verifying || nextKey.trim() === ""}>
            {verifying ? "Verifying…" : "Sign in"}
          </button>
        </div>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <p className="hint" role="status" aria-live="polite">
        {apiKey !== "" ? "Session storage holds a previously entered key." : "No key stored in this session."}
      </p>
    </section>
  );
}

async function verifyConnection(apiKey: string, endpoint: string): Promise<void> {
  const api = new AuraApi({ apiKey, endpoint });
  await api.ready();
}