export interface StatusItem {
  label: string;
  value: string;
  percentage: number;
  color?: "green" | "blue" | "yellow" | "red";
}

export interface AIStatusCardProps {
  model: string;
  status: "online" | "offline" | "busy";
  responseTime: string;
  metrics: StatusItem[];
}