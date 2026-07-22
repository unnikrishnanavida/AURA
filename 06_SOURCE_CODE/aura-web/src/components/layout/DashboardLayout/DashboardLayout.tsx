import Sidebar from "../Navbar";
import Topbar from "../Topbar";

import styles from "./DashboardLayout.module.css";

import type { DashboardLayoutProps } from "./DashboardLayout.types";

export default function DashboardLayout({
  children,
  title = "Dashboard",
}: DashboardLayoutProps) {
  return (
    <div className={styles.layout}>
      <Sidebar />

      <div className={styles.content}>
        <Topbar title={title} />

        <main className={styles.main}>
          {children}
        </main>
      </div>
    </div>
  );
}