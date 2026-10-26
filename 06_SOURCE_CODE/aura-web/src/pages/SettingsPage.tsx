/**
 * Settings: General (connection endpoint), Security (access key) and a
 * pointer to the advanced Diagnostic / Security Log surfaces.
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
      <h2>Settings</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          update({ endpoint: nextEndpoint.trim(), apiKey: nextKey });
          setSaved(true);
          window.setTimeout(() => setSaved(false), 1500);
        }}
      >
        <div className="settings-block">
          <h3>General</h3>
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
        </div>
        <div className="settings-block">
          <h3>Security</h3>
          <label>
            Access key (optional)
            <input
              type="password"
              value={nextKey}
              onChange={(e) => setNextKey(e.target.value)}
              autoComplete="off"
              placeholder="leave blank if the server does not require one"
            />
          </label>
          <p className="hint">Your key is kept in this browser session only and is never written to local storage.</p>
        </div>
        <div className="settings-block">
          <h3>Advanced</h3>
          <p className="hint">
            System diagnostics and a one-click Security Log export live under Advanced in the sidebar, so daily use
            stays simple.
          </p>
        </div>
        <div className="actions">
          <button type="submit">Save</button>
          <button type="button" className="ghost" onClick={clearCredentials}>
            Clear credentials
          </button>
        </div>
      </form>
      {saved ? <p className="ok">Settings saved</p> : null}
    </section>
  );
}