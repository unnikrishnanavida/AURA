import styles from "./Notifications.module.css"
import type { NotificationsProps } from "./Notifications.types"

const Notifications = ({ notifications }: NotificationsProps) => (
  <section className={styles.card}>
    <h2>Notifications</h2>
    {notifications.length === 0 ? (
      <p>No notifications</p>
    ) : (
      <ul>
        {notifications.map((notification) => (
          <li key={notification.id}>{notification.message}</li>
        ))}
      </ul>
    )}
  </section>
);

export default Notifications;
