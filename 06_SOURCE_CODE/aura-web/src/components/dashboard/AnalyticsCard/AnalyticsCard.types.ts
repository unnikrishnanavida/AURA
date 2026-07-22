import type { LucideIcon } from "lucide-react";

export interface AnalyticsMetric {
    id: string;
    title: string;
    value: string | number;
    change: string;
    trend: "up" | "down" | "neutral";
    icon: LucideIcon;
}

export interface AnalyticsCardProps {
    title?: string;
    metrics: AnalyticsMetric[];
    onViewReport?: () => void;
}