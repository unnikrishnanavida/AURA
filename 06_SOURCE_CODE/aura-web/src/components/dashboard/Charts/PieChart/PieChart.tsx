import {
    Cell,
    Legend,
    Pie,
    PieChart as RechartsPieChart,
    ResponsiveContainer,
    Tooltip,
} from "recharts";

import styles from "./PieChart.module.css";
import type { PieChartProps } from "./PieChart.types";

const PieChart = ({
    data,
    height = 320,
    innerRadius = 0,
    outerRadius = 100,
    showLegend = true,
    showTooltip = true,
    showLabels = true,
}: PieChartProps) => {

    return (

        <div
            className={styles.container}
            style={{ height }}
        >

            <ResponsiveContainer
                width="100%"
                height="100%"
            >

                <RechartsPieChart>

                    <Pie
                        data={data}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={innerRadius}
                        outerRadius={outerRadius}
                        paddingAngle={3}
                        label={
                            showLabels
                                ? ({ percent }: { percent?: number }) =>
                                      `${(
                                          (percent ?? 0) * 100
                                      ).toFixed(0)}%`
                                : false
                        }
                    >

                        {data.map((entry) => (

                            <Cell
                                key={entry.id}
                                fill={entry.color}
                            />

                        ))}

                    </Pie>

                    {showTooltip && (
                        <Tooltip />
                    )}

                    {showLegend && (
                        <Legend />
                    )}

                </RechartsPieChart>

            </ResponsiveContainer>

        </div>

    );

};

export default PieChart;