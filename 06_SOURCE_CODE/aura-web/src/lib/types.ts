/**
 * Domain types mirroring the canonical AURA API payloads.
 *
 * Every type corresponds to a real field the API returns; nothing here is
 * fabricated demo data.
 */

/** Memory record returned by /v1/recall. */
export interface MemoryEntry {
  id: string;
  key: string;
  kind: string;
  content: Record<string, unknown>;
}

/** Knowledge claim returned by /v1/retrieve. */
export interface ClaimEntry {
  claim_id: string;
  statement: string;
  predicate: string[];
  status: string;
  confidence: number;
  trust: number;
}

/** Research finding returned by /v1/research. */
export interface Finding {
  claim: string;
  status: string;
  confidence: number;
  evidence_count: number;
  supporting: string[];
  contradicting: string[];
}

/** Research output envelope. */
export interface ResearchOutput {
  question: string;
  findings: Finding[];
  synthesis: string;
  overall_confidence: number;
  epistemic: string;
  contradictions: string[][];
}

/** One research run returned by GET /v1/research/runs. */
export interface ResearchRun {
  run_id: string;
  status: string;
  question: string;
  findings_count: number | null;
  epistemic: string | null;
  started_at: string | null;
}

/** Page envelope returned by GET /v1/research/runs. */
export interface ResearchRunsPage {
  runs: ResearchRun[];
  next_cursor: number | null;
  count: number;
  limit: number;
}

/** One audit record from /v1/audit. */
export interface AuditRecord {
  action: string;
  actor: string;
  resource: string;
  decision: string;
  reason: string;
  timestamp: string;
  correlation_id: string | null;
}

/** One security log entry returned by POST /v1/security/logs. */
export interface SecurityLogEntry {
  action: string;
  actor: string;
  resource: string;
  decision: string;
  reason: string;
  timestamp: string;
  correlation_id: string | null;
}

/** Reasoning result envelope. */
/** One retrieved, attributable piece of context behind an answer. */
export interface GroundingItem {
  source: "memory" | "knowledge" | string;
  reference: string;
  text: string;
  score: number;
  confidence: number;
  belief: number;
  verified: boolean;
  contradicted: boolean;
  scope: string | null;
  provenance: Record<string, unknown>;
}

/** The explicit context AURA assembled for one request. */
export interface ReasoningContext {
  items: GroundingItem[];
  contradictions: string[][];
  dropped: number;
  truncated: boolean;
  filtered: number;
  turns: number;
}

/** Canonical provider outcome vocabulary (mirrors aura/providers/result.py). */
export type ProviderStatus =
  | "ok"
  | "not_configured"
  | "unauthorized"
  | "unavailable"
  | "model_unavailable"
  | "authentication_failed"
  | "forbidden"
  | "timeout"
  | "cancelled"
  | "rate_limited"
  | "transient_failure"
  | "malformed_response"
  | "unsupported_capability"
  | "budget_exceeded";

/**
 * What AURA can truthfully say about one provider.
 *
 * `registered` is not `configured`, and `configured` is not `available`: an
 * adapter existing proves none of them. The frontend must never imply a
 * language model exists because an entry is listed.
 */
export interface ProviderDescriptor {
  name: string;
  kind: string;
  model: string | null;
  local: boolean;
  configured: boolean;
  registered: boolean;
  available: boolean | null;
  privacy_approved: boolean;
  capabilities: string[];
  states: string[];
  timeout_seconds: number;
  cost_per_call: number;
}

export interface ProviderStateResponse {
  language_model_configured: boolean;
  reason?: string;
  configured?: string | null;
  count: number;
  providers: ProviderDescriptor[];
}

export interface ReasonResult {
  execution_id: string;
  correlation_id: string;
  route?: "conversation" | "memory" | string;
  answer: string | null;
  confidence: number | null;
  uncertainty: string | null;
  steps: Array<{ stage: string; detail: string }>;
  provider?: {
    status: ProviderStatus | null;
    name: string | null;
    model: string | null;
    local: boolean | null;
    synthesized: boolean;
    /** Always false for model output: a provider answer is not verified truth. */
    verified: boolean;
    mode?: "generation" | "synthesis" | string;
  } | null;
  /** True when the answer came from retrieved context rather than a model. */
  grounded?: boolean;
  /** Why AURA declined to answer, when it declined. */
  abstention_reason?: string;
  context?: ReasoningContext;
  /** Slice 1D: the cancellable request id (returned on every reason response). */
  request_id?: string;
  /** Overall request lifecycle: "ok" when completed, "cancelled" when stopped. */
  status?: "ok" | "cancelled" | "error";
  /** Where cancellation was observed when status === "cancelled". */
  cancelled_stage?: string;
}

/**
 * Status of one cancellable request (GET /v1/tasks/{id}). The future "Stop
 * button" polls this while a request is in flight.
 */
export interface TaskStatus {
  request_id: string;
  status: "running" | "ok" | "cancelled" | "error";
  stage: string;
  cancelled_stage: string | null;
  created_at: number;
  finished_at: number | null;
  result: ReasonResult | null;
  error: string | null;
}

/** Acknowledged cancellation request (POST /v1/tasks/{id}/cancel). */
export interface TaskCancelled {
  request_id: string;
  status: "cancelling";
}

/** One flight-recorder event from an agent run. */
export interface AgentEvent {
  event_type: string;
  payload: Record<string, unknown>;
  event_id: string;
  timestamp: string;
  execution_id?: string | null;
  agent_id?: string | null;
  goal_id?: string | null;
}

/** Outcome of POST /v1/agents/run (owner-scoped, cancellable). */
export interface AgentRunResult {
  request_id: string;
  status: "ok" | "cancelled" | "error";
  agent_id: string | null;
  goal_id: string | null;
  success: boolean;
  reason: string;
  iterations: number;
  final_message: string;
  cancelled: boolean;
  cancelled_stage?: string;
  events: AgentEvent[];
  /** Phase 1I: verification/reflection/learning-candidate outcome. */
  evaluation?: {
    verification_status: "verified" | "failed" | "cancelled" | "inconclusive";
    verification_reason?: string;
    reflection_summary?: string;
    signals?: Array<{ kind: string; content: string; confidence: number }>;
    learning_status: "none" | "candidate";
    candidate_id?: string | null;
    candidate_content?: string | null;
    evidence_count?: number;
  } | null;
}

/** Plan result envelope. */
export interface PlanResult {
  plan_created: boolean;
  plan_id: string | null;
  steps: string[];
  risk: string | null;
  issues: string[];
}

/** Health envelope from /health. */
export interface HealthResult {
  status: string;
  service: string;
}

/** Readiness envelope from /ready. */
export interface ReadyResult {
  status: string;
  details: Record<string, unknown>;
}

/** Metric snapshot from /v1/metrics. */
export interface MetricSnapshot {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  latency: Record<string, { count: number; avg_seconds: number; max_seconds: number }>;
}