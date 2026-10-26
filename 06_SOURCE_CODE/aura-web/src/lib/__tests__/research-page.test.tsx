/**
 * Component tests for the Research workspace runs history.
 * The page renders exclusively from real-shaped API payloads via stubbed fetch.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsProvider } from "../settings";
import { ResearchPage } from "../../pages/ResearchPage";

function ResearchHarness() {
  return (
    <SettingsProvider>
      <ResearchPage />
    </SettingsProvider>
  );
}

describe("ResearchPage runs list", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  function stubRuns(payload: object, status = 200) {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(payload), { status })) as unknown as typeof fetch,
    );
  }

  it("renders real runs with status and findings count", async () => {
    stubRuns({
      runs: [
        {
          run_id: "ex-1",
          status: "completed",
          question: "is the sky blue?",
          findings_count: 3,
          epistemic: "evidence",
          started_at: "2026-01-01T00:00:00+00:00",
        },
      ],
      next_cursor: null,
      count: 1,
      limit: 20,
    });
    render(<ResearchHarness />);
    await waitFor(() => {
      expect(screen.getByText("is the sky blue?")).toBeTruthy();
    });
    expect(screen.getByText(/completed · evidence/)).toBeTruthy();
    expect(screen.getByText(/3 finding/)).toBeTruthy();
    expect(screen.getByText(/2026-01-01/)).toBeTruthy();
  });

  it("shows the empty state without fabricating metrics", async () => {
    stubRuns({ runs: [], next_cursor: null, count: 0, limit: 20 });
    render(<ResearchHarness />);
    await waitFor(() => {
      expect(screen.getByText(/No research runs recorded yet/)).toBeTruthy();
    });
    expect(screen.queryByText(/0 finding/)).toBeNull();
  });

  it("handles missing optional fields safely", async () => {
    stubRuns({
      runs: [
        {
          run_id: "ex-2",
          status: "completed",
          question: "legacy run",
          findings_count: null,
          epistemic: null,
          started_at: null,
        },
      ],
      next_cursor: null,
      count: 1,
      limit: 20,
    });
    render(<ResearchHarness />);
    await waitFor(() => {
      expect(screen.getByText("legacy run")).toBeTruthy();
    });
    expect(screen.getByText("—")).toBeTruthy();
  });

  it("shows an API failure and retries successfully", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockRejectedValueOnce(new TypeError("boom"))
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ runs: [], next_cursor: null, count: 0, limit: 20 }), {
            status: 200,
          }),
        ),
    );
    render(<ResearchHarness />);
    await waitFor(() => {
      expect(screen.getByText(/boom/)).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Retry loading runs" }));
    await waitFor(() => {
      expect(screen.getByText(/No research runs recorded yet/)).toBeTruthy();
    });
  });
});