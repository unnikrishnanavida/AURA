import {
  Search,
  Bell,
  Sparkles,
  UserCircle2,
} from "lucide-react";

import styles from "./Topbar.module.css";
import type { TopbarProps } from "./Topbar.types";

export default function Topbar({
  title = "Dashboard",
}: TopbarProps) {
  return (
    <header className={styles.topbar}>
      <div>
        <h1>{title}</h1>
      </div>

      <div className={styles.actions}>
        <div className={styles.search}>
          <Search size={18} />

          <input
            placeholder="Search anything..."
          />
        </div>

        <div className={styles.status}>
          <Sparkles size={16} />

          <span>AI Online</span>
        </div>

        <button className={styles.iconButton}>
          <Bell size={20} />
        </button>

        <button className={styles.profile}>
          <UserCircle2 size={42} />
        </button>
      </div>
    </header>
  );
}