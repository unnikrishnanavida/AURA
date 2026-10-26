/** Real Overview dashboard data from existing endpoints (no synthetic metrics). */
export interface OverviewAuditEntry {
  action: string;
  decision: string;
  reason: string;
}
export interface OverviewData {
  executionCount: number;
  rateLimitDenials: number;
  knowledgeCount: number;
  memoryCount: number;
  memoryBackend: string;
  audit: OverviewAuditEntry[];
}

async function getJson<T>(endpoint: string, path: string, apiKey: string): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
  const res = await fetch(`${endpoint}${path}`, { headers });
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return (await res.json()) as T;
}

export async function fetchOverview(endpoint: string, apiKey = ""): Promise<OverviewData> {
  const [metrics, graph, stats, audit] = await Promise.all([
    getJson<{ counters?: Record<string, number> }>(endpoint, "/v1/metrics", apiKey),
    getJson<{ count: number }>(endpoint, "/v1/knowledge/graph", apiKey).catch(() => ({ count: 0 })),
    getJson<{ count: number; backend: string }>(endpoint, "/v1/memory/stats", apiKey),
    getJson<{ entries: OverviewAuditEntry[] }>(endpoint, "/v1/audit", apiKey),
  ]);
  return {
    executionCount: metrics.counters?.execution_count ?? 0,
    rateLimitDenials: metrics.counters?.rate_limit_deny ?? 0,
    knowledgeCount: graph.count,
    memoryCount: stats.count,
    memoryBackend: stats.backend,
    audit: audit.entries ?? [],
  };
}