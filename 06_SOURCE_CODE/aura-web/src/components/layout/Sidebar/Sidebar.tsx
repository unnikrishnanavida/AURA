import {
  LayoutDashboard,
  Brain,
  Database,
  BookOpen,
  FlaskConical,
  Bot,
  BarChart3,
  Settings,
  LogOut,
} from "lucide-react";

import styles from "./Sidebar.module.css";
import type { SidebarItem, SidebarProps } from "./Sidebar.types";

const menuItems: SidebarItem[] = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/dashboard",
  },
  {
    title: "Brain",
    icon: Brain,
    path: "/brain",
  },
  {
    title: "Memory",
    icon: Database,
    path: "/memory",
  },
  {
    title: "Knowledge",
    icon: BookOpen,
    path: "/knowledge",
  },
  {
    title: "Laboratory",
    icon: FlaskConical,
    path: "/laboratory",
  },
  {
    title: "Agents",
    icon: Bot,
    path: "/agents",
  },
  {
    title: "Analytics",
    icon: BarChart3,
    path: "/analytics",
  },
  {
    title: "Settings",
    icon: Settings,
    path: "/settings",
  },
];

export default function Sidebar({
  collapsed = false,
}: SidebarProps) {
  return (
    <aside
      className={`${styles.sidebar} ${
        collapsed ? styles.collapsed : ""
      }`}
    >
      <div className={styles.logo}>
        <div className={styles.logoIcon}>A</div>

        {!collapsed && (
          <span>AURA</span>
        )}
      </div>

      <nav className={styles.nav}>
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <a
              key={item.title}
              href={item.path}
              className={styles.link}
            >
              <Icon size={22} />

              {!collapsed && (
                <span>{item.title}</span>
              )}
            </a>
          );
        })}
      </nav>

      <button className={styles.logout}>
        <LogOut size={20} />

        {!collapsed && (
          <span>Logout</span>
        )}
      </button>
    </aside>
  );
}