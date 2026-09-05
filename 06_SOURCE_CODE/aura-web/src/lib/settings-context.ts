/**
 * Settings context + hook. Kept separate from the provider component so the
 * component file stays react-refresh friendly (components only).
 */

import { createContext, useContext } from "react";
import { AuraApi } from "./api";

export interface Settings {
  endpoint: string;
  apiKey: string;
  api: AuraApi;
  update: (next: { endpoint?: string; apiKey?: string }) => void;
  clearCredentials: () => void;
}

export const SettingsContext = createContext<Settings | null>(null);

export function useSettings(): Settings {
  const value = useContext(SettingsContext);
  if (value === null) {
    throw new Error("useSettings must be used inside <SettingsProvider>");
  }
  return value;
}