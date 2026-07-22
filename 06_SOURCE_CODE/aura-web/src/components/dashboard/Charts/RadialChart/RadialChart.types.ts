export interface RadialChartData {
    name: string;
    value: number;
    fill: string;
}

export interface RadialChartProps {
    data: RadialChartData[];
    height?: number;
    innerRadius?: number | string;
    outerRadius?: number | string;
    startAngle?: number;
    endAngle?: number;
    centerLabel?: string;
    centerValue?: string | number;
    showTooltip?: boolean;
}