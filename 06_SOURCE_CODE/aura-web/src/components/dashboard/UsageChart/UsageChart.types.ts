export interface UsageChartData {
    label: string;
    value: number;
}

export interface UsageChartProps {
    title?: string;
    subtitle?: string;
    data: UsageChartData[];
    chart: React.ReactNode;
    onViewAnalytics?: () => void;
}