export interface Notification {
  id: string;
  message: string;
}

export interface NotificationsProps {
  notifications: Notification[];
}
