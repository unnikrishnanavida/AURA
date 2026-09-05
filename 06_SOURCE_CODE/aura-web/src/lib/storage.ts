/**
 * Secure storage strategy for the web client.
 *
 * The API key is NEVER written to localStorage (persistent storage). It is kept
 * only in sessionStorage, which the browser clears when the tab closes, and is
 * never logged or rendered. Non-secret preferences (endpoint) may use
 * localStorage.
 */

const KEY_SESSION = "aura.api.key";
const KEY_ENDPOINT = "aura.endpoint";

export function readApiKey(): string {
  try {
    return sessionStorage.getItem(KEY_SESSION) ?? "";
  } catch {
    return "";
  }
}

export function writeApiKey(key: string): void {
  try {
    if (key) sessionStorage.setItem(KEY_SESSION, key);
    else sessionStorage.removeItem(KEY_SESSION);
  } catch {
    // private mode: sessionStorage may be unavailable; key stays in memory only
  }
}

export function readEndpoint(): string {
  try {
    return localStorage.getItem(KEY_ENDPOINT) ?? "";
  } catch {
    return "";
  }
}

export function writeEndpoint(endpoint: string): void {
  try {
    if (endpoint) localStorage.setItem(KEY_ENDPOINT, endpoint);
    else localStorage.removeItem(KEY_ENDPOINT);
  } catch {
    // ignore storage failures
  }
}