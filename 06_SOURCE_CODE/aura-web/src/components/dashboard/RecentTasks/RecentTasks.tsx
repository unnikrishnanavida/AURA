import styles from "./RecentTasks.module.css";
import type { RecentTasksProps } from "./RecentTasks.types";
import {
    ChevronRight,
    CalendarDays,
    User,
    Eye,
} from "lucide-react";

const RecentTasks = ({
    tasks,
    onViewTask,
    onViewAll,
}: RecentTasksProps) => {
    return (
        <section className={styles.card}>
            <div className={styles.header}>
                <h2>Recent Tasks</h2>

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

            <div className={styles.list}>
                {tasks.length > 0 ? (
                    tasks.map((task) => (
                        <div
                            key={task.id}
                            className={styles.task}
                        >
                            <div className={styles.top}>
                                <h3>{task.title}</h3>

                                <span
                                    className={`${styles.priority} ${styles[task.priority]}`}
                                >
                                    {task.priority}
                                </span>
                            </div>

                            <div className={styles.meta}>
                                <span>
                                    <User size={15} />
                                    {task.assignee}
                                </span>

                                <span>
                                    <CalendarDays size={15} />
                                    {task.dueDate}
                                </span>
                            </div>

                            <div className={styles.progressBar}>
                                <div
                                    className={styles.progress}
                                    style={{
                                        width: `${task.progress}%`,
                                    }}
                                />
                            </div>

                            <div className={styles.footer}>
                                <span
                                    className={`${styles.status} ${styles[task.status]}`}
                                >
                                    {task.status}
                                </span>

                                {onViewTask && (
                                    <button
                                        type="button"
                                        className={styles.viewBtn}
                                        onClick={() =>
                                            onViewTask(task.id)
                                        }
                                    >
                                        <Eye size={16} />
                                        View
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className={styles.empty}>
                        No tasks available.
                    </div>
                )}
            </div>
        </section>
    );
};

export default RecentTasks;