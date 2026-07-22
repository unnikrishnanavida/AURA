export type HealthStatus =
  | "healthy"
  | "warning"
  | "critical";

export interface HealthMetric {
  id: string;
  name: string;
  value: string;
  usage: number;
  status: HealthStatus;
}

export interface SystemHealthProps {
  metrics: HealthMetric[];
}