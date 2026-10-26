/** Typed client for GET /v1/knowledge/graph (Phase D record-H contracts). */
export interface GraphNode {
  id: string;
  statement: string;
  predicate: string[];
  status: string;
  confidence: number;
  contradicts: string[];
  provenance_source: string | null;
}
export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}
export interface KnowledgeGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  count: number;
}

export async function fetchKnowledgeGraph(
  endpoint: string,
  limit = 200,
  apiKey = "",
): Promise<KnowledgeGraphResponse> {
  const url = `${endpoint}/v1/knowledge/graph?limit=${limit}`;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`knowledge graph request failed (${res.status})`);
  return (await res.json()) as KnowledgeGraphResponse;
}