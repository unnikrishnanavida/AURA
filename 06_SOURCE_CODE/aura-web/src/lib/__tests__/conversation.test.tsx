/**
 * Conversation tests: answer, error + retry, cancel, provider metadata.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SettingsProvider } from "../settings";
import { writeApiKey } from "../storage";
import { Conversation } from "../conversation";

function okReason(payload: Record<string, unknown>) {
  return vi.fn(async () => {
    return new Response(
      JSON.stringify({ execution_id: "ex-1", correlation_id: "co-1", steps: [], ...payload }),
      { status: 200 },
    );
  }) as unknown as typeof fetch;
}

describe("Conversation", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    writeApiKey("k-test");
  });

  it("shows the structured answer and provider metadata", async () => {
    vi.stubGlobal(
      "fetch",
      okReason({ answer: "yes", confidence: 0.9, uncertainty: "low", provider: { name: "live-test", synthesized: true } }),
    );
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );
    const input = screen.getByLabelText("Question");
    fireEvent.change(input, { target: { value: "is it safe?" } });
    fireEvent.click(screen.getByRole("button", { name: "Reason" }));
    await waitFor(() => {
      expect(screen.getByText("yes")).toBeTruthy();
    });
    expect(screen.getByText("live-test")).toBeTruthy();
  });

  it("shows an error turn with retry, and retries successfully", async () => {
    const fail = vi.fn(async () => {
      return new Response(JSON.stringify({ error: { code: "api.error", message: "boom" } }), {
        status: 400,
      });
    }) as unknown as typeof fetch;
    vi.stubGlobal("fetch", fail);
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );
    const input = screen.getByLabelText("Question");
    fireEvent.change(input, { target: { value: "do math" } });
    fireEvent.click(screen.getByRole("button", { name: "Reason" }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });

    vi.stubGlobal("fetch", okReason({ answer: "42", confidence: 1.0, uncertainty: "low" }));
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => {
      expect(screen.getByText("42")).toBeTruthy();
    });
  });

  it("marks a cancelled turn as cancelled (no error)", async () => {
    const never = vi.fn(async (_url: unknown, init: unknown) => {
      const signal = (init as { signal?: AbortSignal }).signal;
      const pending = new Promise<Response>((_resolve, reject) => {
        signal?.addEventListener("abort", () => reject(Object.assign(new Error("aborted"), { name: "AbortError" })));
      });
      return pending;
    }) as unknown as typeof fetch;
    vi.stubGlobal("fetch", never);
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );
    const input = screen.getByLabelText("Question");
    fireEvent.change(input, { target: { value: "long task" } });
    fireEvent.click(screen.getByRole("button", { name: "Reason" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Cancel" })).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => {
      expect(screen.getByText("Cancelled.")).toBeTruthy();
    });
  });
});