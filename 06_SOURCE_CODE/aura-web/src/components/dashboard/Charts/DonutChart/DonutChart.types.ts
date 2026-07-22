export interface DonutChartData {
    id: string;
    name: string;
    value: number;
    color: string;
}

export interface DonutChartProps {
    data: DonutChartData[];
    height?: number;
    innerRadius?: number;
    outerRadius?: number;
    centerLabel?: string;
    centerValue?: string | number;
    showLegend?: boolean;
    showTooltip?: boolean;
}