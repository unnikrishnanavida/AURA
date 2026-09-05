/**
 * Settings: configure the API endpoint and (optionally) an API key.
 */

import { useState } from "react";
import { useSettings } from "../lib/settings-context";

export function SettingsPage() {
  const { endpoint, apiKey, update, clearCredentials } = useSettings();
  const [nextEndpoint, setNextEndpoint] = useState(endpoint);
  const [nextKey, setNextKey] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  return (
    <section aria-label="Settings" className="panel">
      <h2>Connection settings</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          update({ endpoint: nextEndpoint.trim(), apiKey: nextKey });
          setSaved(true);
          window.setTimeout(() => setSaved(false), 1500);
        }}
      >
        <label>
          AURA API endpoint
          <input
            type="url"
            value={nextEndpoint}
            onChange={(e) => setNextEndpoint(e.target.value)}
            placeholder="http://127.0.0.1:8765"
            required
          />
        </label>
        <label>
          API key (optional; kept in session storage only, never in localStorage)
          <input
            type="password"
            value={nextKey}
            onChange={(e) => setNextKey(e.target.value)}
            autoComplete="off"
            placeholder="leave blank if the server does not require one"
          />
        </label>
        <div className="actions">
          <button type="submit">Save</button>
          <button type="button" className="ghost" onClick={clearCredentials}>
            Clear credentials
          </button>
        </div>
      </form>
      {saved ? <p className="ok">Settings saved</p> : null}
      <p className="hint">
        The API key is stored in sessionStorage, which the browser clears when the tab closes.
      </p>
    </section>
  );
}