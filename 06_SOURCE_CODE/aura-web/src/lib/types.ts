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

/** Reasoning result envelope. */
export interface ReasonResult {
  execution_id: string;
  correlation_id: string;
  answer: string | null;
  confidence: number | null;
  uncertainty: string | null;
  steps: Array<{ stage: string; detail: string }>;
  provider?: { name: string; synthesized: boolean } | null;
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