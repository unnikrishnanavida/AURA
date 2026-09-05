import { useState } from "react";
import { AuditPage } from "./pages/AuditPage";
import { ConsolePage } from "./pages/ConsolePage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { MemoryPage } from "./pages/MemoryPage";
import { ResearchPage } from "./pages/ResearchPage";
import { SettingsPage } from "./pages/SettingsPage";
import { StatusPage } from "./pages/StatusPage";
import { useSettings } from "./lib/settings-context";

const TABS = [
  { id: "status", label: "Status", node: <StatusPage /> },
  { id: "console", label: "Reasoning", node: <ConsolePage /> },
  { id: "memory", label: "Memory", node: <MemoryPage /> },
  { id: "knowledge", label: "Knowledge", node: <KnowledgePage /> },
  { id: "research", label: "Research", node: <ResearchPage /> },
  { id: "audit", label: "Audit", node: <AuditPage /> },
  { id: "settings", label: "Settings", node: <SettingsPage /> },
] as const;

type TabId = (typeof TABS)[number]["id"];

function App() {
  const [active, setActive] = useState<TabId>("status");
  const { endpoint } = useSettings();

  const activeTab = TABS.find((t) => t.id === active) ?? TABS[0];

  return (
    <div className="shell">
      <header className="topbar">
        <h1>AURA Console</h1>
        <span className="endpoint" title="Configured AURA API endpoint">
          {endpoint}
        </span>
      </header>
      <nav aria-label="Primary">
        <ul className="tabs">
          {TABS.map((tab) => (
            <li key={tab.id}>
              <button
                type="button"
                className={tab.id === active ? "active" : ""}
                aria-current={tab.id === active ? "page" : undefined}
                onClick={() => setActive(tab.id)}
              >
                {tab.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <main>{activeTab.node}</main>
      <footer>
        <p>Every value shown here is fetched live from the configured AURA API. No demo data is injected.</p>
      </footer>
    </div>
  );
}

export default App;