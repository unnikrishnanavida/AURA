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

  it("serializes an agent run request as JSON", async () => {
    let sent: { url: string; body: string } = { url: "", body: "" };
    globalThis.fetch = vi.fn(async (url, init) => {
      sent = { url: String(url), body: String(init?.body ?? "") };
      return new Response(
        JSON.stringify({
          request_id: "rq-c0ffee",
          status: "ok",
          agent_id: "ag-1",
          goal_id: "goal-1",
          success: false,
          reason: "no capability available",
          iterations: 0,
          final_message: "",
          cancelled: false,
          events: [],
        }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 0 });
    const result = await api.runAgent("organize notes", {
      capabilities: ["notes.write"],
      successCriteria: ["done == True"],
      requestId: "c0ffee",
    });
    expect(result.agent_id).toBe("ag-1");
    expect(sent.url).toMatch(/\/v1\/agents\/run$/);
    expect(JSON.parse(sent.body)).toEqual({
      goal: "organize notes",
      capabilities: ["notes.write"],
      success_criteria: ["done == True"],
      request_id: "c0ffee",
    });
  });
});

describe("AuraApi.listResearchRuns", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("requests the real endpoint with bounded limit and auth header", async () => {
    let seen: { url: string; headers: Record<string, string> } = { url: "", headers: {} };
    globalThis.fetch = vi.fn(async (url, init) => {
      seen = { url: String(url), headers: (init?.headers ?? {}) as Record<string, string> };
      return new Response(
        JSON.stringify({ runs: [], next_cursor: null, count: 0, limit: 20 }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;

    const api = new AuraApi({ apiKey: "tok-a", retries: 0 });
    const page = await api.listResearchRuns(20, 41);
    expect(page.runs).toEqual([]);
    expect(seen.url).toContain("/v1/research/runs?limit=20&cursor=41");
    expect(seen.headers.Authorization).toBe("Bearer tok-a");
  });

  it("parses the real run shapes including nullable optional fields", async () => {
    globalThis.fetch = vi.fn(async () => {
      return new Response(
        JSON.stringify({
          runs: [
            {
              run_id: "ex-1",
              status: "completed",
              question: "is the sky blue?",
              findings_count: 3,
              epistemic: "evidence",
              started_at: "2026-01-01T00:00:00+00:00",
            },
            {
              run_id: "ex-2",
              status: "completed",
              question: "legacy",
              findings_count: null,
              epistemic: null,
              started_at: null,
            },
          ],
          next_cursor: 7,
          count: 2,
          limit: 20,
        }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 0 });
    const page = await api.listResearchRuns();
    expect(page.runs).toHaveLength(2);
    expect(page.runs[1].findings_count).toBeNull();
    expect(page.runs[1].epistemic).toBeNull();
    expect(page.next_cursor).toBe(7);
  });

  it("throws a typed ApiError for non-success responses", async () => {
    globalThis.fetch = vi.fn(async () => {
      return new Response(
        JSON.stringify({ error: { code: "api.validation", message: "field 'limit' must be an integer" } }),
        { status: 400 },
      );
    }) as unknown as typeof fetch;

    const api = new AuraApi({ retries: 0 });
    await expect(api.listResearchRuns(99)).rejects.toMatchObject({
      status: 400,
      code: "api.validation",
    } satisfies Partial<ApiError>);
  });
});
describe("AuraApi.securityLogs", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("POSTs the reason to /v1/security/logs and returns entries", async () => {
    let seen: { url: string; method: string; body: string; headers: Record<string, string> } = {
      url: "",
      method: "",
      body: "",
      headers: {},
    };
    globalThis.fetch = vi.fn(async (url, init) => {
      seen = {
        url: String(url),
        method: String(init?.method ?? ""),
        body: String(init?.body ?? ""),
        headers: (init?.headers ?? {}) as Record<string, string>,
      };
      return new Response(
        JSON.stringify({
          entries: [
            {
              action: "security.logs.requested",
              actor: "user",
              resource: "security-log",
              decision: "allow",
              reason: "support",
              timestamp: "2026-01-01T00:00:00Z",
              correlation_id: "co-1",
            },
          ],
        }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;

    const api = new AuraApi({ apiKey: "tok-a", retries: 0 });
    const result = await api.securityLogs("support");
    expect(seen.url).toContain("/v1/security/logs");
    expect(seen.method).toBe("POST");
    expect(JSON.parse(seen.body)).toEqual({ reason: "support" });
    expect(seen.headers.Authorization).toBe("Bearer tok-a");
    expect(result.entries).toHaveLength(1);
    expect(result.entries[0].action).toBe("security.logs.requested");
  });
});