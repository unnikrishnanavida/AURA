/**
 * Conversation tests: answer, error + retry, cancel, provider metadata.
 * The conversation is driven through the ChatComposer (aria-label
 * "Ask AURA anything" + "Send message" button, "Stop generating" while busy).
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
    const input = screen.getByLabelText("Ask AURA anything");
    fireEvent.change(input, { target: { value: "is it safe?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await waitFor(() => {
      expect(screen.getByText("yes")).toBeTruthy();
    });
    fireEvent.click(screen.getByText("Response details"));
    expect(screen.getByText("live-test")).toBeTruthy();
  });

  it("explains an unconfigured language model instead of a bare refusal", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            answer: "I do not know",
            provider: {
              status: "not_configured",
              name: null,
              model: null,
              local: null,
              synthesized: false,
              verified: false,
            },
            abstention_reason: "no language model is currently configured",
          }),
          { status: 200 },
        ),
      ) as unknown as typeof fetch,
    );
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );
    fireEvent.change(screen.getByPlaceholderText(/ask/i), { target: { value: "What is AI?" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/no language model is currently configured/i)).toBeTruthy();
    });
    expect(screen.queryByText(/couldn't connect/i)).toBeNull();
  });

  it("reports a provider failure differently from a missing provider", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            answer: "I do not know",
            provider: {
              status: "timeout",
              name: null,
              model: null,
              local: null,
              synthesized: false,
              verified: false,
            },
          }),
          { status: 200 },
        ),
      ) as unknown as typeof fetch,
    );
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );
    fireEvent.change(screen.getByPlaceholderText(/ask/i), { target: { value: "What is AI?" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => {
      expect(screen.getByText(/took too long to respond/i)).toBeTruthy();
    });
    expect(screen.queryByText(/no language model is currently configured/i)).toBeNull();
  });

  it("sends prior turns as temporary context for the next message", async () => {
    const requests: Array<{ body: string }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: unknown, init: unknown) => {
        requests.push({ body: (init as { body: string }).body });
        const answer = requests.length === 1 ? "Understood." : "Your project is AURA.";
        return new Response(
          JSON.stringify({ execution_id: "ex-1", correlation_id: "co-1", steps: [], answer }),
          { status: 200 },
        );
      }) as unknown as typeof fetch,
    );
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );

    const input = screen.getByLabelText("Ask AURA anything");
    fireEvent.change(input, { target: { value: "My project is called AURA." } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText("Understood.");

    fireEvent.change(screen.getByLabelText("Ask AURA anything"), { target: { value: "What is my project called?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText("Your project is AURA.");

    const secondRequest = JSON.parse(requests[1].body) as { history: Array<{ role: string; content: string }> };
    expect(secondRequest.history).toEqual([
      { role: "user", content: "My project is called AURA." },
      { role: "assistant", content: "Understood." },
    ]);
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
    const input = screen.getByLabelText("Ask AURA anything");
    fireEvent.change(input, { target: { value: "do math" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
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
    const input = screen.getByLabelText("Ask AURA anything");
    fireEvent.change(input, { target: { value: "long task" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Stop generating" })).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Stop generating" }));
    await waitFor(() => {
      expect(screen.getByText("Stopped.")).toBeTruthy();
    });
  });

  it("clears and invalidates an in-flight response when starting a new chat", async () => {
    let aborted = false;
    const pending = vi.fn(async (_url: unknown, init: unknown) => {
      const signal = (init as { signal?: AbortSignal }).signal;
      return new Promise<Response>((_resolve, reject) => {
        signal?.addEventListener("abort", () => {
          aborted = true;
          reject(Object.assign(new Error("aborted"), { name: "AbortError" }));
        });
      });
    }) as unknown as typeof fetch;
    vi.stubGlobal("fetch", pending);
    render(
      <SettingsProvider>
        <Conversation />
      </SettingsProvider>,
    );

    fireEvent.change(screen.getByLabelText("Ask AURA anything"), { target: { value: "Old question" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByRole("button", { name: "Stop generating" });
    fireEvent.click(screen.getByRole("button", { name: "New chat" }));

    await waitFor(() => expect(aborted).toBe(true));
    expect(screen.getByRole("heading", { name: "How can I help you today?" })).toBeTruthy();
    expect(screen.queryByText("Old question")).toBeNull();
    expect(screen.queryByText("Stopped.")).toBeNull();
  });
});