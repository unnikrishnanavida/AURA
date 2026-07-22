export type TimeRange =
    | "24h"
    | "7d"
    | "30d"
    | "90d"
    | "1y";

export interface KPI {

    id: string;

    title: string;

    value: string;

    change: number;

    trend: "up" | "down";

}

export interface UsagePoint {

    name: string;

    requests: number;

    tokens: number;

    cost: number;

}

export interface ResourceUsage {

    cpu: number;

    gpu: number;

    memory: number;

    storage: number;

}

export interface AnalyticsFilter {

    range: TimeRange;

}

export interface AnalyticsProps {

    className?: string;

}