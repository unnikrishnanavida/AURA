/**
 * Component tests for the settings + console pages using Testing Library.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SettingsProvider } from "../settings";
import { ConsolePage } from "../../pages/ConsolePage";
import { SettingsPage } from "../../pages/SettingsPage";

function ConsoleHarness() {
  return (
    <SettingsProvider>
      <ConsolePage />
    </SettingsProvider>
  );
}

describe("ConsolePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the chat surface", () => {
    render(<ConsoleHarness />);
    expect(screen.getByRole("heading", { name: "How can I help you today?" })).toBeTruthy();
    expect(screen.getByLabelText("Ask AURA anything")).toBeTruthy();
  });

  it("displays a structured answer from the API", async () => {
    const fetchMock = vi.fn(async () => {
      return new Response(
        JSON.stringify({
          execution_id: "ex-1",
          correlation_id: "co-1",
          answer: "yes",
          confidence: 0.9,
          uncertainty: "low",
          steps: [],
        }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;
    vi.stubGlobal("fetch", fetchMock);

    render(<ConsoleHarness />);
    const input = screen.getByLabelText("Ask AURA anything");
    fireEvent.change(input, { target: { value: "is it safe?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));

    await waitFor(() => {
      expect(screen.getByText("yes")).toBeTruthy();
    });
    expect(screen.getAllByText("0.90").length).toBeGreaterThan(0);
  });

  it("shows a friendly error instead of the raw API message", async () => {
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ error: { code: "api.error", message: "boom" } }), {
        status: 500,
      });
    }) as unknown as typeof fetch;
    vi.stubGlobal("fetch", fetchMock);

    render(<ConsoleHarness />);
    const input = screen.getByLabelText("Ask AURA anything");
    fireEvent.change(input, { target: { value: "x?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
    expect(screen.queryByText(/boom/)).toBeNull();
  });
});

describe("SettingsPage", () => {
  it("persists endpoint into the provider state", () => {
    render(
      <SettingsProvider>
        <SettingsPage />
      </SettingsProvider>,
    );
    const endpoint = screen.getByLabelText("AURA API endpoint");
    fireEvent.change(endpoint, { target: { value: "http://127.0.0.1:9999" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(screen.getByText(/Settings saved/)).toBeTruthy();
  });
});