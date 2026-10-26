/**
 * Component tests for the interactive Knowledge Graph page.
 * Renders exclusively from real-shaped API payloads via stubbed fetch.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsProvider } from "../settings";
import { KnowledgeGraphPage } from "../../pages/KnowledgeGraphPage";

function GraphHarness() {
  return (
    <SettingsProvider>
      <KnowledgeGraphPage />
    </SettingsProvider>
  );
}

const GRAPH_PAYLOAD = {
  nodes: [
    {
      id: "cl-1",
      statement: "fast deployment is safe",
      predicate: ["deployment"],
      status: "evidence",
      confidence: 0.91,
      contradicts: ["cl-2"],
      provenance_source: "audit:test",
    },
    {
      id: "cl-2",
      statement: "fast deployment is not safe",
      predicate: ["deployment"],
      status: "hypothesis",
      confidence: 0.62,
      contradicts: ["cl-1"],
      provenance_source: null,
    },
  ],
  edges: [
    { source: "cl-1", target: "cl-2", type: "contradicts" },
    { source: "cl-2", target: "cl-1", type: "contradicts" },
  ],
  count: 2,
};

describe("KnowledgeGraphPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the interactive graph from real API data and shows the legend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(GRAPH_PAYLOAD), { status: 200 })) as unknown as typeof fetch,
    );
    render(<GraphHarness />);

    await waitFor(() => {
      expect(document.querySelector("svg.graph-svg")).toBeTruthy();
    });
    expect(screen.getByText(/2 claim\(s\) · 2 relationship edge\(s\)/)).toBeTruthy();
    expect(screen.getAllByText(/contradicts/).length).toBeGreaterThan(0);
  });

  it("selects a node with the keyboard and shows real stored details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(GRAPH_PAYLOAD), { status: 200 })) as unknown as typeof fetch,
    );
    const { container } = render(<GraphHarness />);
    await waitFor(() => {
      expect(document.querySelectorAll(".graph-node").length).toBe(2);
    });

    const first = container.querySelector<HTMLElement>(".graph-node");
    expect(first).toBeTruthy();
    fireEvent.keyDown(first as HTMLElement, { key: "ArrowRight" });
    await waitFor(() => {
      expect(container.querySelector(".graph-node.selected")).toBeTruthy();
    });
    const focused = container.querySelector<HTMLElement>(".graph-node.selected");
    fireEvent.keyDown(focused as HTMLElement, { key: "Enter" });

    await waitFor(() => {
      expect(screen.getByText("Selected node")).toBeTruthy();
    });
    expect(screen.getAllByText(/evidence/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/0\.910/).length).toBeGreaterThan(0);
    expect(screen.getByText("audit:test")).toBeTruthy();
    expect(screen.getAllByText(/fast deployment is not safe/).length).toBeGreaterThan(0);
  });

  it("renders the accessible list alternative with the same live data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(GRAPH_PAYLOAD), { status: 200 })) as unknown as typeof fetch,
    );
    render(<GraphHarness />);
    await waitFor(() => {
      expect(document.querySelector("svg.graph-svg")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Accessible list" }));
    await waitFor(() => {
      expect(screen.getByRole("table", { name: "Knowledge claims" })).toBeTruthy();
    });
    expect(screen.getByText("fast deployment is safe")).toBeTruthy();
  });

  it("shows the empty state when the knowledge store is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () => new Response(JSON.stringify({ nodes: [], edges: [], count: 0 }), { status: 200 }),
      ) as unknown as typeof fetch,
    );
    render(<GraphHarness />);
    await waitFor(() => {
      expect(screen.getByText(/No persisted claims/)).toBeTruthy();
    });
  });

  it("shows an error and recovers via retry", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockRejectedValueOnce(new TypeError("network down"))
        .mockResolvedValueOnce(new Response(JSON.stringify(GRAPH_PAYLOAD), { status: 200 })),
    );
    render(<GraphHarness />);
    await waitFor(() => {
      expect(screen.getByText(/network down/)).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Retry loading graph" }));
    await waitFor(() => {
      expect(document.querySelector("svg.graph-svg")).toBeTruthy();
    });
  });
});