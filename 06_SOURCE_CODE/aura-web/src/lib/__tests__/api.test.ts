/**
 * API client tests: error mapping, retry, timeout, auth header, serialization.
 */

import { describe, expect, it, vi, afterEach } from "vitest";
import { AuraApi, ApiError } from "../api";

describe("AuraApi", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("maps a 500 response to a typed ApiError with the server code", async () => {
    globalThis.fetch = vi.fn(async () => {
      return new Response(JSON.stringify({ error: { code: "api.error", message: "boom" } }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 0 });
    await expect(api.health()).rejects.toMatchObject({
      status: 500,
      code: "api.error",
      message: "boom",
    } satisfies Partial<ApiError>);
  });

  it("retries a 503 then succeeds", async () => {
    let calls = 0;
    globalThis.fetch = vi.fn(async () => {
      calls += 1;
      if (calls === 1) {
        return new Response(JSON.stringify({ error: { code: "api.error", message: "unavailable" } }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 2 });
    const health = await api.health();
    expect(health.status).toBe("ok");
    expect(calls).toBe(2);
  });

  it("throws a typed timeout error on abort", async () => {
    globalThis.fetch = vi.fn(async (_url, init) => {
      const controller = init?.signal as AbortSignal | undefined;
      return new Promise<Response>((_resolve, reject) => {
        controller?.addEventListener("abort", () => {
          const err = new DOMException("aborted", "AbortError");
          reject(err);
        });
      });
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 0, timeoutMs: 1 });
    await expect(api.health()).rejects.toMatchObject({ code: "sdk.timeout" });
  });

  it("sends the bearer token only when configured", async () => {
    let seenHeaders: Record<string, string> = {};
    globalThis.fetch = vi.fn(async (_url, init) => {
      const raw = (init?.headers ?? {}) as Record<string, string>;
      seenHeaders = raw;
      return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
    }) as unknown as typeof fetch;

    const api = new AuraApi({ apiKey: "web-test-key-123456", retries: 0 });
    await api.health();
    expect(seenHeaders["Authorization"]).toBe("Bearer web-test-key-123456");
  });
});

describe("AuraApi request/response serialization", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("serializes a reason request as JSON", async () => {
    let sentBody = "";
    globalThis.fetch = vi.fn(async (_url, init) => {
      sentBody = String(init?.body ?? "");
      return new Response(
        JSON.stringify({ execution_id: "ex-1", answer: "yes", confidence: 0.9 }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 0 });
    const result = await api.reason("is it safe?", { safe: 0.9 });
    expect(result.answer).toBe("yes");
    expect(JSON.parse(sentBody)).toEqual({ question: "is it safe?", facts: { safe: 0.9 } });
  });
});