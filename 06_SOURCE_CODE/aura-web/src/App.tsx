import { useState } from "react";
import {
  BookOpen,
  Database,
  FileText,
  FlaskConical,
  House,
  Network,
  Settings,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";
import { AuraLogo } from "./components/aura/AuraLogo";
import { ProfileMenu } from "./components/chat/ProfileMenu";
import { StatusPill } from "./components/chat/StatusPill";
import { AuthGate } from "./lib/auth-gate";
import { DiagnosticsPage } from "./pages/DiagnosticsPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { HomePage } from "./pages/HomePage";
import { KnowledgeGraphPage } from "./pages/KnowledgeGraphPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { MemoryPage } from "./pages/MemoryPage";
import { ResearchPage } from "./pages/ResearchPage";
import { SecurityLogPage } from "./pages/SecurityLogPage";
import { SettingsPage } from "./pages/SettingsPage";

const NAV_GROUPS = [
  {
    group: "Workspace",
    items: [
      { id: "home", label: "Home", icon: House },
      { id: "memory", label: "Memory", icon: Database },
      { id: "documents", label: "Documents", icon: FileText },
      { id: "research", label: "Research", icon: FlaskConical },
    ],
  },
  {
    group: "Knowledge",
    items: [
      { id: "knowledge", label: "Knowledge", icon: BookOpen },
      { id: "graph", label: "Knowledge Graph", icon: Network },
    ],
  },
  {
    group: "Advanced",
    items: [
      { id: "diagnostics", label: "Diagnostics", icon: Stethoscope },
      { id: "security", label: "Security Log", icon: ShieldCheck },
      { id: "settings", label: "Settings", icon: Settings },
    ],
  },
] as const;

type TabId = (typeof NAV_GROUPS)[number]["items"][number]["id"];

const ACTIVE_LABELS = NAV_GROUPS.map((g) => g.items).flat() as Array<{ id: TabId; label: string }>;

function App() {
  const [active, setActive] = useState<TabId>("home");
  const [drawerOpen, setDrawerOpen] = useState(false);

  const activeLabel = ACTIVE_LABELS.find((item) => item.id === active)?.label ?? "Home";

  function navigate(id: string) {
    setActive(id as TabId);
    setDrawerOpen(false);
  }

  function renderPage() {
    const homePage = <HomePage onNavigate={navigate} />;
    switch (active) {
      case "home":
        return homePage;
      case "memory":
        return <MemoryPage />;
      case "documents":
        return <DocumentsPage />;
      case "research":
        return <ResearchPage />;
      case "knowledge":
        return <KnowledgePage />;
      case "graph":
        return <KnowledgeGraphPage />;
      case "diagnostics":
        return <DiagnosticsPage />;
      case "security":
        return <SecurityLogPage />;
      case "settings":
        return <SettingsPage />;
      default:
        return homePage;
    }
  }

  return (
    <AuthGate>
      <div className="shell">
        <header className="topbar">
          <button
            type="button"
            className="menu-toggle"
            aria-label="Toggle navigation"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen((open) => !open)}
          >
            Menu
          </button>
          <AuraLogo variant="horizontal" className="topbar-logo" />
          <h1>{activeLabel}</h1>
          <StatusPill />
          <ProfileMenu onNavigate={navigate} />
        </header>
        <div className="shell-body">
          <aside className={drawerOpen ? "sidebar is-open" : "sidebar"} aria-label="Sidebar">
            <div className="brand" aria-label="AURA">
              <AuraLogo variant="horizontal" className="brand-logo" />
            </div>
            <nav aria-label="Primary" className="sidebar-nav">
              {NAV_GROUPS.map((group) => (
                <section key={group.group} aria-label={group.group}>
                  <h2>{group.group}</h2>
                  <ul>
                    {group.items.map((item) => (
                      <li key={item.id}>
                        <button
                          type="button"
                          className={item.id === active ? "active" : ""}
                          aria-current={item.id === active ? "page" : undefined}
                          onClick={() => navigate(item.id)}
                        >
                          <item.icon aria-hidden="true" />
                          {item.label}
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </nav>
            <p className="sidebar-foot">AURA · The AI Ecosystem</p>
          </aside>
          <div
            className={drawerOpen ? "sidebar-scrim is-open" : "sidebar-scrim"}
            onClick={() => setDrawerOpen(false)}
            aria-hidden="true"
          />
          <main className={active === "home" ? "content chat-active" : "content"}>{renderPage()}</main>
        </div>
      </div>
    </AuthGate>
  );
}

export default App;