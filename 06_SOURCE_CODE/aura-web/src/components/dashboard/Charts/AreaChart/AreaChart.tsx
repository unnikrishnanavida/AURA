import {
    Area,
    AreaChart as RechartsAreaChart,
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import styles from "./AreaChart.module.css";
import type { AreaChartProps } from "./AreaChart.types";

const AreaChart = ({
    data,
    series,
    xAxisKey,
    height = 320,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
}: AreaChartProps) => {

    return (

        <div
            className={styles.container}
            style={{ height }}
        >

            <ResponsiveContainer
                width="100%"
                height="100%"
            >

                <RechartsAreaChart data={data}>

                    <defs>

                        {series.map((item) => (

                            <linearGradient
                                key={item.key}
                                id={`gradient-${item.key}`}
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >

                                <stop
                                    offset="5%"
                                    stopColor={item.color}
                                    stopOpacity={0.45}
                                />

                                <stop
                                    offset="95%"
                                    stopColor={item.color}
                                    stopOpacity={0.03}
                                />

                            </linearGradient>

                        ))}

                    </defs>

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

                        <Area
                            key={item.key}
                            type="monotone"
                            dataKey={item.key}
                            name={item.name}
                            stroke={item.color}
                            strokeWidth={3}
                            fill={`url(#gradient-${item.key})`}
                            activeDot={{
                                r: 6,
                            }}
                        />

                    ))}

                </RechartsAreaChart>

            </ResponsiveContainer>

        </div>

    );

};

export default AreaChart;