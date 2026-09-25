/**
 * AuthGate tests: sign-in flow, credential errors, session sign-out.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SettingsProvider } from "../settings";
import { writeApiKey } from "../storage";
import { AuthGate } from "../auth-gate";

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
      expect(screen.getByText(/rejected \(401\)/)).toBeTruthy();
    });
    expect(screen.queryByText("dashboard")).toBeNull();
  });

  it("signs out and returns to the sign-in panel", () => {
    writeApiKey("k-stored");
    render(
      <SettingsProvider>
        <AuthGate>
          <span>dashboard</span>
        </AuthGate>
      </SettingsProvider>,
    );
    expect(screen.getByText("dashboard")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(screen.getByRole("heading", { name: "Sign in to AURA" })).toBeTruthy();
  });
});