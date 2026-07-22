export interface ChartLegendItem {
    id: string;
    label: string;
    color: string;
    value?: string | number;
}

export interface ChartLegendProps {
    items: ChartLegendItem[];
    direction?: "row" | "column";
    className?: string;
}