/**
 * StatusPill — minimal "AURA Online" indicator derived from the real
 * /health + /ready probes. No raw endpoint or technical detail surfaced.
 */

import { useEffect, useState } from "react";
import { useSettings } from "../../lib/settings-context";

type PillState = "connecting" | "online" | "offline";

const POLL_MS = 30_000;

export function StatusPill() {
  const { api } = useSettings();
  const [state, setState] = useState<PillState>("connecting");

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    async function probe() {
      try {
        const [h, r] = await Promise.all([api.health(), api.ready()]);
        if (cancelled) return;
        const online =
          h.status === "ok" &&
          (r.status === "ok" || r.status === "ready" || r.status === undefined);
        setState(online ? "online" : "offline");
      } catch {
        if (!cancelled) setState("offline");
      }
      timer = window.setTimeout(() => void probe(), POLL_MS);
    }

    void probe();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [api]);

  const label = state === "online" ? "AURA Online" : state === "offline" ? "AURA Offline" : "Connecting…";

  return (
    <span className={`status-pill ${state}`} role="status" aria-live="polite" title="Live AURA connection status">
      <span className="status-pill-dot" aria-hidden="true" />
      {label}
    </span>
  );
}