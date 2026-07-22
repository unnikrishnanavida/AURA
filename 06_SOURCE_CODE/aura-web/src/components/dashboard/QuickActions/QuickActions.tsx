import styles from "./QuickActions.module.css";
import { ArrowUpRight } from "lucide-react";
import type { QuickActionsProps } from "./QuickActions.types";

const QuickActions = ({ actions }: QuickActionsProps) => {
  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <h3>Quick Actions</h3>
        <span>{actions.length} Actions</span>
      </div>

      <div className={styles.grid}>
        {actions.map((action) => {
          const Icon = action.icon;

          return (
            <button
              key={action.id}
              className={styles.action}
              onClick={action.onClick}
              type="button"
            >
              <div className={styles.icon}>
                <Icon size={22} />
              </div>

              <div className={styles.content}>
                <h4>{action.title}</h4>

                {action.subtitle && (
                  <p>{action.subtitle}</p>
                )}
              </div>

              <ArrowUpRight
                size={18}
                className={styles.arrow}
              />
            </button>
          );
        })}
      </div>
    </section>
  );
};

export default QuickActions;