/**
 * Minimal typed HTTP client for the canonical AURA API.
 *
 * Focused on the endpoints the web app actually uses. Every request carries a
 * timeout and an optional bearer token; transient transport failures are
 * retried with bounded backoff. No demo data is injected anywhere.
 */

import type {
  AuditRecord,
  AgentRunResult,
  ClaimEntry,
  HealthResult,
  MemoryEntry,
  MetricSnapshot,
  PlanResult,
  ProviderStateResponse,
  ReadyResult,
  ReasonResult,
  ResearchOutput,
  ResearchRunsPage,
  SecurityLogEntry,
  TaskCancelled,
  TaskStatus,
} from "./types";

export interface ApiConfig {
  endpoint: string;
  apiKey: string;
  timeoutMs: number;
  retries: number;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const DEFAULT_ENDPOINT = "http://127.0.0.1:8765";

const RETRYABLE_STATUS = new Set([408, 429, 500, 502, 503, 504]);
const RETRYABLE_CODES = new Set(["sdk.timeout", "sdk.transport"]);

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class AuraApi {
  readonly config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = {
      endpoint: DEFAULT_ENDPOINT,
      apiKey: "",
      timeoutMs: 15_000,
      retries: 2,
      ...config,
    };
  }

  withKey(apiKey: string): AuraApi {
    return new AuraApi({ ...this.config, apiKey });
  }

  private async request<T>(
    method: "GET" | "POST",
    path: string,
    body?: Record<string, unknown>,
    options?: { signal?: AbortSignal },
  ): Promise<T> {
    const url = `${this.config.endpoint}${path}`;
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (this.config.apiKey) {
      headers.Authorization = `Bearer ${this.config.apiKey}`;
    }
    let attempt = 0;
    for (;;) {
      attempt += 1;
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.config.timeoutMs);
        const wireSignal = options?.signal
          ? AbortSignal.any([controller.signal, options.signal])
          : controller.signal;
        let response: Response;
        try {
          response = await fetch(url, {
            method,
            headers,
            body: body === undefined ? undefined : JSON.stringify(body),
            signal: wireSignal,
          });
        } finally {
          clearTimeout(timer);
        }
        const payload = (await response.json()) as unknown;
        if (!response.ok) {
          const err = (payload as { error?: { code?: string; message?: string } }).error ?? {};
          const code = err.code ?? "api.error";
          if (this.shouldRetry(response.status, code, attempt)) {
            await sleep(150 * 2 ** (attempt - 1));
            continue;
          }
          throw new ApiError(response.status, code, err.message ?? response.statusText);
        }
        return payload as T;
      } catch (error) {
        if (options?.signal?.aborted) {
          throw new ApiError(0, "sdk.cancelled", "cancelled");
        }
        const isAbort = error instanceof DOMException && error.name === "AbortError";
        if (isAbort) {
          if (this.shouldRetry(0, "sdk.timeout", attempt)) {
            await sleep(100);
            continue;
          }
          throw new ApiError(0, "sdk.timeout", "request timed out");
        }
        if (error instanceof ApiError) throw error;
        // A transport failure (DNS, refused connection, TLS, offline) is a real,
        // nameable condition. Without this it escapes as a bare TypeError and
        // every UI reports it as a generic "couldn't connect".
        throw new ApiError(
          0,
          "sdk.transport",
          error instanceof Error ? error.message : "network request failed",
        );
      }
    }
  }

  private shouldRetry(status: number, code: string, attempt: number): boolean {
    if (attempt > this.config.retries) return false;
    return RETRYABLE_STATUS.has(status) || RETRYABLE_CODES.has(code);
  }

  // -- endpoints ------------------------------------------------------------
  health(): Promise<HealthResult> {
    return this.request<HealthResult>("GET", "/health");
  }

  ready(): Promise<ReadyResult> {
    return this.request<ReadyResult>("GET", "/ready");
  }

  reason(
    question: string,
    facts?: Record<string, number>,
    signal?: AbortSignal,
    history?: Array<{ role: "user" | "assistant"; content: string }>,
    requestId?: string,
  ): Promise<ReasonResult> {
    const payload: {
      question: string;
      facts: Record<string, number>;
      history?: Array<{ role: "user" | "assistant"; content: string }>;
      request_id?: string;
    } = { question, facts: facts ?? {} };
    if (history?.length) payload.history = history;
    if (requestId) payload.request_id = requestId;
    return this.request<ReasonResult>("POST", "/v1/reason", payload, { signal });
  }

  /** Poll the status of one request (owner-scoped; powers the future Stop button). */
  getTask(requestId: string, signal?: AbortSignal): Promise<TaskStatus> {
    return this.request<TaskStatus>("GET", `/v1/tasks/${requestId}`, undefined, { signal });
  }

  /** Ask the server to cancel an in-flight request (owner-scoped). */
  cancelTask(requestId: string, signal?: AbortSignal): Promise<TaskCancelled> {
    return this.request<TaskCancelled>("POST", `/v1/tasks/${requestId}/cancel`, undefined, { signal });
  }

  /** Run one goal through the guarded agent runtime (owner-scoped). */
  runAgent(
    goal: string,
    options: {
      capabilities?: string[];
      successCriteria?: string[];
      worldState?: Record<string, unknown>;
      requestId?: string;
      signal?: AbortSignal;
    } = {},
  ): Promise<AgentRunResult> {
    const payload: Record<string, unknown> = { goal };
    if (options.successCriteria?.length) payload.success_criteria = options.successCriteria;
    if (options.capabilities?.length) payload.capabilities = options.capabilities;
    if (options.worldState) payload.world_state = options.worldState;
    if (options.requestId) payload.request_id = options.requestId;
    return this.request<AgentRunResult>("POST", "/v1/agents/run", payload, { signal: options.signal });
  }

  remember(key: string, content: Record<string, unknown>, kind = "episodic"): Promise<{ memory_id: string }> {
    return this.request<{ memory_id: string }>("POST", "/v1/remember", { key, content, kind });
  }

  recall(text: string, limit = 10, signal?: AbortSignal): Promise<{ entries: MemoryEntry[] }> {
    return this.request<{ entries: MemoryEntry[] }>("POST", "/v1/recall", { text, limit }, { signal });
  }

  observe(statement: string, predicate: string[] = []): Promise<{ claim_id: string }> {
    return this.request<{ claim_id: string }>("POST", "/v1/observe", { statement, predicate });
  }

  retrieve(statement?: string, limit = 10): Promise<{ claims: ClaimEntry[] }> {
    return this.request<{ claims: ClaimEntry[] }>("POST", "/v1/retrieve", { statement: statement ?? "", limit });
  }

  research(question: string, claims: string[] = []): Promise<ResearchOutput> {
    return this.request<ResearchOutput>("POST", "/v1/research", { question, claims });
  }

  listResearchRuns(limit = 20, cursor?: number, signal?: AbortSignal): Promise<ResearchRunsPage> {
    const query = new URLSearchParams({ limit: String(limit) });
    if (cursor !== undefined) query.set("cursor", String(cursor));
    return this.request<ResearchRunsPage>("GET", `/v1/research/runs?${query.toString()}`, undefined, { signal });
  }

  plan(goal: string, tasks: Array<{ name: string; capability?: string; risk?: number }>): Promise<PlanResult> {
    return this.request<PlanResult>("POST", "/v1/plan", { goal, tasks });
  }

  metrics(): Promise<MetricSnapshot> {
    return this.request<MetricSnapshot>("GET", "/v1/metrics");
  }

  audit(): Promise<{ entries: AuditRecord[] }> {
    return this.request<{ entries: AuditRecord[] }>("GET", "/v1/audit");
  }

  /**
   * Explicitly request the security log (e.g., for support). The server
   * records the request as its own audit event and serves the live log.
   */
  securityLogs(reason?: string): Promise<{ entries: SecurityLogEntry[] }> {
    return this.request<{ entries: SecurityLogEntry[] }>("POST", "/v1/security/logs", { reason: reason ?? "" });
  }

  /** Provider discovery: what is registered, configured and actually available. */
  providerState(signal?: AbortSignal): Promise<ProviderStateResponse> {
    return this.request<ProviderStateResponse>("GET", "/v1/providers", undefined, { signal });
  }
}

export { DEFAULT_ENDPOINT };