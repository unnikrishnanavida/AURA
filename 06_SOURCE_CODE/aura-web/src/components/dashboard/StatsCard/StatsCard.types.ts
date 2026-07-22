import type { LucideIcon } from "lucide-react";

export interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend: "up" | "down" | "neutral";
  trendValue: string;
  subtitle?: string;
  onClick?: () => void;
}