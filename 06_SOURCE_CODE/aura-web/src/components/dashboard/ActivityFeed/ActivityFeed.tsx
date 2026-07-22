import styles from "./ActivityFeed.module.css";
import ActivityCard from "../ActivityCard";
import type { ActivityFeedProps } from "./ActivityFeed.types";
import { ChevronRight } from "lucide-react";

const ActivityFeed = ({
  title = "Recent Activity",
  activities,
  onViewAll,
}: ActivityFeedProps) => {
  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <h2>{title}</h2>

        {onViewAll && (
          <button
            type="button"
            className={styles.viewAll}
            onClick={onViewAll}
          >
            View All
            <ChevronRight size={18} />
          </button>
        )}
      </div>

      <div className={styles.feed}>
        {activities.length > 0 ? (
          activities.map((activity, index) => (
            <ActivityCard
              key={`${activity.title}-${index}`}
              {...activity}
            />
          ))
        ) : (
          <div className={styles.empty}>
            No recent activity available.
          </div>
        )}
      </div>
    </section>
  );
};

export default ActivityFeed;