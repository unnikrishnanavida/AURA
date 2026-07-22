export interface AreaChartSeries {
    key: string;
    name: string;
    color: string;
}

export interface AreaChartData {
    [key: string]: string | number;
}

export interface AreaChartProps {
    data: AreaChartData[];
    series: AreaChartSeries[];
    xAxisKey: string;
    height?: number;
    showGrid?: boolean;
    showLegend?: boolean;
    showTooltip?: boolean;
}