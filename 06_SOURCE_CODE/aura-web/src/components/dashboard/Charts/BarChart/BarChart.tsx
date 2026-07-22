import {
    Bar,
    BarChart as RechartsBarChart,
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import styles from "./BarChart.module.css";
import type { BarChartProps } from "./BarChart.types";

const BarChart = ({
    data,
    series,
    xAxisKey,
    height = 320,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
}: BarChartProps) => {

    return (

        <div
            className={styles.container}
            style={{ height }}
        >

            <ResponsiveContainer
                width="100%"
                height="100%"
            >

                <RechartsBarChart
                    data={data}
                    barGap={6}
                    barCategoryGap="20%"
                >

                    {showGrid && (

                        <CartesianGrid
                            stroke="#2A2F38"
                            strokeDasharray="3 3"
                        />

                    )}

                    <XAxis
                        dataKey={xAxisKey}
                        stroke="#9CA3AF"
                        tickLine={false}
                        axisLine={false}
                    />

                    <YAxis
                        stroke="#9CA3AF"
                        tickLine={false}
                        axisLine={false}
                    />

                    {showTooltip && (
                        <Tooltip />
                    )}

                    {showLegend && (
                        <Legend />
                    )}

                    {series.map((item) => (

                        <Bar
                            key={item.key}
                            dataKey={item.key}
                            name={item.name}
                            fill={item.color}
                            radius={[8, 8, 0, 0]}
                            stackId={item.stackId}
                        />

                    ))}

                </RechartsBarChart>

            </ResponsiveContainer>

        </div>

    );

};

export default BarChart;