/**
 * Session context + hook. Kept separate from the AuthGate component so the
 * component file stays react-refresh friendly (components only).
 */

import { createContext, useContext } from "react";

export interface Session {
  signedIn: boolean;
  signOut: () => void;
}

export const SessionContext = createContext<Session | null>(null);

export function useSession(): Session {
  const value = useContext(SessionContext);
  if (value === null) {
    throw new Error("useSession must be used inside <AuthGate>");
  }
  return value;
}