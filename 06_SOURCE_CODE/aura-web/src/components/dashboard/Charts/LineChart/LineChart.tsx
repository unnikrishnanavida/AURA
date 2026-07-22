import {
    CartesianGrid,
    Legend,
    Line,
    LineChart as RechartsLineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import styles from "./LineChart.module.css";
import type { LineChartProps } from "./LineChart.types";

const LineChart = ({
    data,
    series,
    xAxisKey,
    height = 320,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
}: LineChartProps) => {

    return (

        <div
            className={styles.container}
            style={{ height }}
        >

            <ResponsiveContainer
                width="100%"
                height="100%"
            >

                <RechartsLineChart data={data}>

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

                        <Line
                            key={item.key}
                            type="monotone"
                            dataKey={item.key}
                            name={item.name}
                            stroke={item.color}
                            strokeWidth={3}
                            dot={false}
                            activeDot={{
                                r: 6,
                            }}
                        />

                    ))}

                </RechartsLineChart>

            </ResponsiveContainer>

        </div>

    );

};

export default LineChart;