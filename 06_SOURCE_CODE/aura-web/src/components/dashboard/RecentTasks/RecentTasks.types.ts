export type TaskStatus =
  | "completed"
  | "in-progress"
  | "pending"
  | "overdue";

export type TaskPriority =
  | "low"
  | "medium"
  | "high";

export interface TaskItem {
  id: string;
  title: string;
  assignee: string;
  dueDate: string;
  progress: number;
  status: TaskStatus;
  priority: TaskPriority;
}

export interface RecentTasksProps {
  tasks: TaskItem[];
  onViewTask?: (taskId: string) => void;
  onViewAll?: () => void;
}