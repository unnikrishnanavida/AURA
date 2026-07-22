export interface ActivityCardProps {
  id: string;
  title: string;
  description?: string;
  timestamp?: string;
  status?: "info" | "success" | "warning" | "error";
}
