import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchKnowledgeGraph, type GraphEdge, type KnowledgeGraphResponse } from "../lib/graph";
import { useSettings } from "../lib/settings-context";

/**
 * Client-side render cap (defense in depth; the server already bounds to 500).
 * Nodes beyond the cap are never rendered and the truncation is called out.
 */
const NODE_CAP = 200;
const EDGE_CAP = 4000;
const VIEW_W = 900;
const VIEW_H = 640;

interface Position {
  x: number;
  y: number;
}

/** Deterministic radial layout: one center + concentric rings, stable per node index. */
function nodePositions(count: number): Position[] {
  const positions: Position[] = [];
  if (count === 0) return positions;
  const cx = VIEW_W / 2;
  const cy = VIEW_H / 2 - 30;
  positions.push({ x: cx, y: cy });
  const baseRadius = 96;
  let layer = 0;
  let index = 1;
  let layerStart = 1;
  while (index < count) {
    layer += 1;
    const radius = baseRadius * layer;
    const perLayer = Math.max(1, Math.floor((2 * Math.PI * radius) / 104));
    const angleStep = (2 * Math.PI) / perLayer;
    for (let k = 0; k < perLayer && index < count; k += 1, index += 1) {
      const angle = (index - layerStart) * angleStep - Math.PI / 2;
      positions.push({ x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) });
    }
    layerStart = index;
  }
  return positions;
}

function truncate(text: string, max = 26): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

export function KnowledgeGraphPage() {
  const { endpoint, apiKey } = useSettings();
  const [data, setData] = useState<KnowledgeGraphResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"graph" | "list">("graph");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    fetchKnowledgeGraph(endpoint, 200, apiKey)
      .then((next) => {
        setData(next);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [endpoint, apiKey]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const { nodes, edges, byId, layout, truncatedNodes } = useMemo(() => {
    const sorted = [...(data?.nodes ?? [])].sort((a, b) => a.id.localeCompare(b.id));
    const capped = sorted.slice(0, NODE_CAP);
    const byIdLocal = new Map(capped.map((n) => [n.id, n]));
    const renderedEdges: GraphEdge[] = [];
    for (const edge of data?.edges ?? []) {
      if (byIdLocal.has(edge.source) && byIdLocal.has(edge.target)) {
        renderedEdges.push(edge);
        if (renderedEdges.length >= EDGE_CAP) break;
      }
    }
    return {
      nodes: capped,
      edges: renderedEdges,
      byId: byIdLocal,
      layout: nodePositions(capped.length),
      truncatedNodes: sorted.length > NODE_CAP,
    };
  }, [data]);

  const selectedNode = selectedId ? (byId.get(selectedId) ?? null) : null;
  const selectedEdges = selectedNode
    ? edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
    : [];

  function selectNode(id: string) {
    setSelectedId((current) => (current === id ? null : id));
  }

  function moveSelection(delta: number) {
    if (nodes.length === 0) return;
    const index = nodes.findIndex((n) => n.id === selectedId);
    const next = index < 0 ? 0 : (index + delta + nodes.length) % nodes.length;
    setSelectedId(nodes[next].id);
  }

  function handleKeyDown(e: React.KeyboardEvent, id: string) {
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      moveSelection(1);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      moveSelection(-1);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setSelectedId(id);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setSelectedId(null);
    } else if (e.key === "Home") {
      e.preventDefault();
      setSelectedId(nodes[0]?.id ?? null);
    } else if (e.key === "End") {
      e.preventDefault();
      setSelectedId(nodes[nodes.length - 1]?.id ?? null);
    }
  }

  const graphView = (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      className="graph-svg"
      role="img"
      aria-label="Knowledge graph visualization. Use arrow keys to move between nodes, Enter to select, Escape to clear."
    >
      {edges.map((edge) => {
        const s = byId.get(edge.source);
        const t = byId.get(edge.target);
        const si = nodes.findIndex((n) => n.id === edge.source);
        const ti = nodes.findIndex((n) => n.id === edge.target);
        const sp = si >= 0 ? layout[si] : undefined;
        const tp = ti >= 0 ? layout[ti] : undefined;
        if (!s || !t || !sp || !tp) return null;
        return (
          <line
            key={`${edge.source}|${edge.target}|${edge.type}`}
            x1={sp.x}
            y1={sp.y}
            x2={tp.x}
            y2={tp.y}
            className={edge.type === "contradicts" ? "graph-edge contradicts" : "graph-edge"}
          >
            <title>
              {s.statement} —{edge.type}→ {t.statement}
            </title>
          </line>
        );
      })}
      {nodes.map((node, index) => {
        const pos = layout[index];
        const isSelected = selectedId === node.id;
        return (
          <g
            key={node.id}
            tabIndex={0}
            role="button"
            aria-label={`Node ${node.statement}. Status ${node.status}.`}
            className={isSelected ? "graph-node selected" : "graph-node"}
            transform={`translate(${pos.x}, ${pos.y})`}
            onClick={() => selectNode(node.id)}
            onKeyDown={(e) => handleKeyDown(e, node.id)}
          >
            <circle r={13} className="graph-node-circle" />
            <title>
              {node.statement} ({node.status}) · confidence{" "}
              {Number.isFinite(node.confidence) ? node.confidence.toFixed(3) : "n/a"}
            </title>
            <text y={-20} textAnchor="middle" className="graph-node-label" aria-hidden="true">
              {truncate(node.statement)}
            </text>
          </g>
        );
      })}
    </svg>
  );

  const listView = (
    <table className="panel" aria-label="Knowledge claims">
      <thead>
        <tr>
          <th scope="col">Statement</th>
          <th scope="col">Status</th>
          <th scope="col">Confidence</th>
          <th scope="col">Provenance</th>
        </tr>
      </thead>
      <tbody>
        {nodes.map((node) => (
          <tr key={node.id}>
            <td>{node.statement}</td>
            <td>{node.status}</td>
            <td>{Number.isFinite(node.confidence) ? node.confidence.toFixed(3) : "—"}</td>
            <td>{node.provenance_source ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <section aria-label="Knowledge graph" className="panel">
      <h2>Knowledge graph</h2>
      {error ? (
        <>
          <p className="error" role="alert">{error}</p>
          <button type="button" className="ghost" onClick={refresh}>
            Retry loading graph
          </button>
        </>
      ) : null}
      {data === null && !error ? <p className="hint">Loading real knowledge…</p> : null}
      {data !== null && data.nodes.length === 0 ? (
        <p className="hint">No persisted claims in the knowledge store yet.</p>
      ) : null}
      {data !== null && data.nodes.length > 0 ? (
        <>
          <div className="kg-toolbar">
            <p className="hint">
              {data.count} claim(s) · {edges.length} relationship edge(s) — read directly from the live knowledge
              store.
              {truncatedNodes ? ` Limit: rendering first ${NODE_CAP} of ${data.nodes.length} nodes.` : ""}
            </p>
            <div className="kg-view-toggle" role="group" aria-label="Knowledge graph display mode">
              <button type="button" aria-pressed={view === "graph"} onClick={() => setView("graph")}>
                Visual graph
              </button>
              <button type="button" aria-pressed={view === "list"} onClick={() => setView("list")}>
                Accessible list
              </button>
            </div>
          </div>
          <p className="hint graph-legend" aria-live="polite">
            Dashed edges are contradiction relationships (type “contradicts”); solid edges are other recorded
            relationship types. Use arrow keys to move through nodes, Enter to select, Escape to clear.
          </p>
          {view === "graph" ? graphView : listView}
          {view === "graph" ? (
            <aside
              className="kg-details"
              aria-label={selectedNode ? "Selected node details" : "Node details"}
            >
              {selectedNode ? (
                <>
                  <h3>Selected node</h3>
                  <h4>{selectedNode.statement}</h4>
                  <dl className="kg-dl">
                    <dt>Status</dt>
                    <dd>{selectedNode.status}</dd>
                    <dt>Confidence</dt>
                    <dd>
                      {Number.isFinite(selectedNode.confidence) ? selectedNode.confidence.toFixed(3) : "—"}
                    </dd>
                    <dt>Provenance</dt>
                    <dd>{selectedNode.provenance_source ?? "—"}</dd>
                    {selectedNode.predicate.length > 0 ? (
                      <>
                        <dt>Predicate</dt>
                        <dd>{selectedNode.predicate.join(", ")}</dd>
                      </>
                    ) : null}
                    <dt>Relationships</dt>
                    <dd>
                      {selectedEdges.length > 0 ? (
                        <ul className="list">
                          {selectedEdges.map((edge) => {
                            const otherId = edge.source === selectedNode.id ? edge.target : edge.source;
                            const other = byId.get(otherId);
                            const outbound = edge.source === selectedNode.id;
                            return (
                              <li key={`${edge.source}|${edge.target}|${edge.type}`}>
                                {outbound ? `—${edge.type}→ ` : `←${edge.type}— `}
                                {other?.statement ?? otherId}
                              </li>
                            );
                          })}
                        </ul>
                      ) : (
                        <span className="hint">No recorded edges reference this node.</span>
                      )}
                    </dd>
                  </dl>
                </>
              ) : (
                <p className="hint">Select a node (click or focus it and press Enter) to inspect its real details.</p>
              )}
            </aside>
          ) : (
            <p className="hint">
              The table above is the equally valid accessible representation of the same live data.
            </p>
          )}
        </>
      ) : null}
    </section>
  );
}