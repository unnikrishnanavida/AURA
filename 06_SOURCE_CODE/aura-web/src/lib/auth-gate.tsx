/**
 * Authentication gate for the AURA web client.
 *
 * When no session exists a branded, full-screen sign-in is shown (centered
 * AURA logo + access key). On success the app shell is revealed via
 * <AuthGate>{children}</AuthGate>. The access key is kept in session storage
 * only. Friendly errors; never renders stored credentials.
 */

import { useState, type FormEvent, type ReactNode } from "react";
import { AuraLogo } from "../components/aura/AuraLogo";
import { AuraApi, ApiError } from "./api";
import { SessionContext } from "./session-context";
import { useSettings } from "./settings-context";

export function AuthGate({ children }: { children: ReactNode }) {
  const { endpoint, apiKey, update, clearCredentials } = useSettings();
  const [signedIn, setSignedIn] = useState(apiKey !== "");
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextKey, setNextKey] = useState(apiKey);

  if (signedIn) {
    return (
      <SessionContext.Provider value={{ signedIn: true, signOut: () => { clearCredentials(); setSignedIn(false); setNextKey(""); setError(null); } }}>
        <div data-testid="auth-session" className="auth-session">
          {children}
        </div>
      </SessionContext.Provider>
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
      setError(friendlyConnectionError(err));
    } finally {
      setVerifying(false);
    }
  }

  return (
    <main className="signin-screen">
      <div className="signin-glow" aria-hidden="true" />
      <section aria-label="Sign in" className="panel signin">
        <AuraLogo variant="stacked" className="signin-logo" />
        <h2>Sign in to AURA</h2>
        <p className="signin-lede">Enter your access key to continue to your AI ecosystem.</p>
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
          <div className="actions">
            <button type="submit" disabled={verifying || nextKey.trim() === ""}>
              {verifying ? "Verifying…" : "Sign in"}
            </button>
          </div>
        </form>
        {error ? <p className="error" role="alert">{error}</p> : null}
        <details className="signin-advanced">
          <summary>Connection details</summary>
          <p className="hint">
            Endpoint: <span className="endpoint">{endpoint}</span> · change it in Settings after signing in.
          </p>
        </details>
        <p className="hint signin-foot" role="status" aria-live="polite">
          {apiKey !== "" ? "Session storage holds a previously entered key." : "Your key stays in this browser session only."}
        </p>
      </section>
    </main>
  );
}

function friendlyConnectionError(err: unknown): string {
  // Each condition gets its own honest message: "couldn't connect" hides the
  // difference between a stopped server, a rejected key, and a key that is
  // valid but not allowed to do this.
  if (err instanceof ApiError) {
    if (err.code === "api.forbidden" || err.status === 403) {
      return "That key is valid but isn't allowed to connect. Ask whoever issued it for access to this AURA instance.";
    }
    if (err.code === "api.auth_failed" || err.status === 401) {
      return "The access key was rejected. Check it and try again.";
    }
    if (err.status === 0) return "AURA couldn't be reached. Check that the connection is running, then try again.";
    if (err.status === 503) return "AURA is running but not ready yet. Try again in a moment.";
    return "AURA couldn't connect right now. Please check the connection and try again.";
  }
  return "AURA couldn't connect right now. Please check the connection and try again.";
}

async function verifyConnection(apiKey: string, endpoint: string): Promise<void> {
  const api = new AuraApi({ apiKey, endpoint });
  await api.ready();
}