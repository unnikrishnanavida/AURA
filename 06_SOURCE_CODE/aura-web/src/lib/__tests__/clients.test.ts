import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchKnowledgeGraph } from "../graph";
import { NotesClient } from "../notes";

function stubFetch(status: number, data: unknown) {
  const fn = vi.fn(async () => ({ ok: status < 400, status, json: async () => data }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => vi.unstubAllGlobals());

describe("fetchKnowledgeGraph", () => {
  it("calls the real endpoint shape and returns nodes/edges", async () => {
    stubFetch(200, { nodes: [{ id: "cl-1" }], edges: [], count: 1 });
    const result = await fetchKnowledgeGraph("http://x:8765", 50, "k");
    expect(result.count).toBe(1);
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "http://x:8765/v1/knowledge/graph?limit=50",
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer k" }) }),
    );
  });

  it("throws on a non-OK response", async () => {
    stubFetch(500, {});
    await expect(fetchKnowledgeGraph("http://x:8765", 200, "k")).rejects.toThrow("knowledge graph");
  });
});

describe("NotesClient", () => {
  it("creates, lists, updates, and deletes with the real request shapes", async () => {
    const fetchMock = vi.fn(async (_input: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      const path = (String(_input).split("?")[0] ?? "").split("/v1/notes")[1] ?? "";
      if (method === "POST")
        return { status: 201, json: async () => ({ note_id: "mem-1", title: "t", content: "c", scope: "owner:a", created_at: null }) };
      if (path === "") return { status: 200, json: async () => ({ notes: [{ note_id: "mem-1", title: "t", content: "c", scope: "owner:a", created_at: null }], count: 1 }) };
      if (method === "PATCH") return { status: 200, json: async () => ({ note_id: "mem-1", title: "t2", content: "c2", scope: "owner:a", created_at: null }) };
      if (method === "DELETE") return { status: 200, json: async () => ({ note_id: "mem-1", deleted: true, scope: "owner:a" }) };
      return { status: 200, json: async () => ({ note_id: "mem-1", title: "t", content: "c", scope: "owner:a", created_at: null }) };
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new NotesClient("http://x:8765", "", "owner:a");
    const created = await client.create({ title: "t", content: "c" });
    expect(created.note_id).toBe("mem-1");
    const listed = await client.list();
    expect(listed).toHaveLength(1);
    const updated = await client.update("mem-1", { title: "t2", content: "c2" });
    expect(updated.content).toBe("c2");
    const removed = await client.remove("mem-1");
    expect(removed).toBe(true);
    expect(fetchMock).toHaveBeenCalled();
  });

  it("throws when the server rejects", async () => {
    stubFetch(400, {});
    await expect(new NotesClient("http://x:8765", "k", "owner:a").create({ title: "", content: "x" })).rejects.toThrow(
      "failed (400)",
    );
  });
});