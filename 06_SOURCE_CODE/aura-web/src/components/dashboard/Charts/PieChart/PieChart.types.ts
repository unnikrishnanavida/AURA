export interface PieChartData {
    id: string;
    name: string;
    value: number;
    color: string;
}

export interface PieChartProps {
    data: PieChartData[];
    height?: number;
    innerRadius?: number;
    outerRadius?: number;
    showLegend?: boolean;
    showTooltip?: boolean;
    showLabels?: boolean;
}