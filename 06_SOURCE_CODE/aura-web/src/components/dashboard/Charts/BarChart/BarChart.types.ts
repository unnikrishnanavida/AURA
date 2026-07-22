export interface BarChartSeries {
    key: string;
    name: string;
    color: string;
    stackId?: string;
}

export interface BarChartData {
    [key: string]: string | number;
}

export interface BarChartProps {
    data: BarChartData[];
    series: BarChartSeries[];
    xAxisKey: string;
    height?: number;
    showGrid?: boolean;
    showLegend?: boolean;
    showTooltip?: boolean;
}