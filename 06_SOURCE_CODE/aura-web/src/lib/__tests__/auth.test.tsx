/**
 * AuthGate tests: sign-in flow, credential errors, session sign-out.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SettingsProvider } from "../settings";
import { writeApiKey } from "../storage";
import { AuthGate } from "../auth-gate";
import { useSession } from "../session-context";

function readyOk() {
  return vi.fn(async () => {
    return new Response(JSON.stringify({ dependency: { ok: true } }), { status: 200 });
  }) as unknown as typeof fetch;
}

describe("AuthGate", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    writeApiKey("");
    // Clean sessionStorage used by the settings provider.
    try {
      sessionStorage.clear();
    } catch {
      /* storage may be memory-backed in this test env */
    }
  });

  it("shows the sign-in panel when no key is stored", () => {
    render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    expect(screen.getByRole("heading", { name: "Sign in to AURA" })).toBeTruthy();
    expect(screen.queryByText("dashboard")).toBeNull();
  });

  it("unlocks content after a successful verification", async () => {
    vi.stubGlobal("fetch", readyOk());
    render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    const keyInput = screen.getByLabelText("API key");
    fireEvent.change(keyInput, { target: { value: "k-test" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => {
      expect(screen.getByText("dashboard")).toBeTruthy();
    });
  });

  it("shows a credential error on 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(
          JSON.stringify({ error: { code: "api.auth_failed", message: "authentication required" } }),
          { status: 401 },
        );
      }) as unknown as typeof fetch,
    );
    render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    const keyInput = screen.getByLabelText("API key");
    fireEvent.change(keyInput, { target: { value: "k-wrong" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => {
      expect(screen.getByText(/access key was rejected/)).toBeTruthy();
    });
    expect(screen.queryByText("dashboard")).toBeNull();
  });

  it("distinguishes a rejected key (401) from an unauthorized key (403)", async () => {
    function respond(status: number, code: string) {
      return vi.fn(async () =>
        new Response(JSON.stringify({ error: { code, message: "denied" } }), { status }),
      ) as unknown as typeof fetch;
    }

    vi.stubGlobal("fetch", respond(401, "api.auth_failed"));
    const unauthorized = render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    fireEvent.change(screen.getByLabelText(/API key/i), { target: { value: "k-nope" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => {
      expect(screen.getByText(/access key was rejected/i)).toBeTruthy();
    });
    unauthorized.unmount();

    vi.stubGlobal("fetch", respond(403, "api.forbidden"));
    render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    fireEvent.change(screen.getByLabelText(/API key/i), { target: { value: "k-limited" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => {
      expect(screen.getByText(/isn't allowed to connect/i)).toBeTruthy();
    });
    // The two conditions must never share the same message.
    expect(screen.queryByText(/access key was rejected/i)).toBeNull();
    expect(screen.queryByText("dashboard")).toBeNull();
  });

  it("reports an unreachable server differently from a rejected key", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }) as unknown as typeof fetch,
    );
    render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    fireEvent.change(screen.getByLabelText(/API key/i), { target: { value: "k-any" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => {
      expect(screen.getByText(/couldn't be reached/i)).toBeTruthy();
    });
    expect(screen.queryByText(/access key was rejected/i)).toBeNull();
  });

  it("signs out through the session context and returns to the sign-in panel", () => {
    writeApiKey("k-stored");
    function Harness() {
      const { signedIn, signOut } = useSession();
      return (
        <>
          {signedIn ? <span>dashboard</span> : null}
          {signedIn ? (
            <button type="button" onClick={signOut}>
              Sign out
            </button>
          ) : null}
        </>
      );
    }
    render(
      <SettingsProvider>
        <AuthGate>
          <Harness />
        </AuthGate>
      </SettingsProvider>,
    );
    expect(screen.getByText("dashboard")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(screen.getByRole("heading", { name: "Sign in to AURA" })).toBeTruthy();
  });
});