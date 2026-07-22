export interface LineChartSeries {
    key: string;
    name: string;
    color: string;
}

export interface LineChartData {
    [key: string]: string | number;
}

export interface LineChartProps {
    data: LineChartData[];
    series: LineChartSeries[];
    xAxisKey: string;
    height?: number;
    showGrid?: boolean;
    showLegend?: boolean;
    showTooltip?: boolean;
}