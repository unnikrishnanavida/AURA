import {
    Cell,
    Legend,
    Pie,
    PieChart as RechartsPieChart,
    ResponsiveContainer,
    Text,
    Tooltip,
} from "recharts";

import styles from "./DonutChart.module.css";
import type { DonutChartProps } from "./DonutChart.types";

const DonutChart = ({
    data,
    height = 320,
    innerRadius = 70,
    outerRadius = 110,
    centerLabel,
    centerValue,
    showLegend = true,
    showTooltip = true,
}: DonutChartProps) => {

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
                        stroke="none"
                        
                    >

                        {data.map((item) => (

                            <Cell
                                key={item.id}
                                fill={item.color}
                            />

                        ))}

                        {(centerLabel || centerValue) && (

                            <Text
                                x="50%"
                                y="46%"
                                textAnchor="middle"
                                fill="#9CA3AF"
                                fontSize={14}
                            >
                                {centerLabel}
                            </Text>

                        )}

                        {centerValue && (

                            <Text
                                x="50%"
                                y="57%"
                                textAnchor="middle"
                                fill="#F8FAFC"
                                fontSize={26}
                                fontWeight={700}
                            >
                                {centerValue}
                            </Text>

                        )}

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

export default DonutChart;