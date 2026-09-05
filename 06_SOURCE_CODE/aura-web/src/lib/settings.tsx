/**
 * Client settings: endpoint + optional API key, persisted per the secure
 * storage strategy in storage.ts.
 */

import { useCallback, useMemo, useState, type ReactNode } from "react";
import { AuraApi, DEFAULT_ENDPOINT } from "./api";
import { SettingsContext } from "./settings-context";
import { readApiKey, readEndpoint, writeApiKey, writeEndpoint } from "./storage";

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [endpoint, setEndpoint] = useState<string>(() => readEndpoint() || DEFAULT_ENDPOINT);
  const [apiKey, setApiKey] = useState<string>(() => readApiKey());

  const api = useMemo(() => new AuraApi({ endpoint, apiKey }), [endpoint, apiKey]);

  const update = useCallback(
    (next: { endpoint?: string; apiKey?: string }) => {
      if (next.endpoint !== undefined) {
        writeEndpoint(next.endpoint);
        setEndpoint(next.endpoint);
      }
      if (next.apiKey !== undefined) {
        writeApiKey(next.apiKey);
        setApiKey(next.apiKey);
      }
    },
    [],
  );

  const clearCredentials = useCallback(() => {
    writeApiKey("");
    setApiKey("");
  }, []);

  const value = useMemo(
    () => ({ endpoint, apiKey, api, update, clearCredentials }),
    [endpoint, apiKey, api, update, clearCredentials],
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export type { Settings } from "./settings-context";