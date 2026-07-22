import {
    PolarAngleAxis,
    RadialBar,
    RadialBarChart,
    ResponsiveContainer,
    Text,
    Tooltip,
} from "recharts";

import styles from "./RadialChart.module.css";
import type { RadialChartProps } from "./RadialChart.types";

const RadialChart = ({
    data,
    height = 320,
    innerRadius = "65%",
    outerRadius = "95%",
    startAngle = 90,
    endAngle = -270,
    centerLabel,
    centerValue,
    showTooltip = true,
}: RadialChartProps) => {

    return (

        <div
            className={styles.container}
            style={{ height }}
        >

            <ResponsiveContainer
                width="100%"
                height="100%"
            >

                <RadialBarChart
                    data={data}
                    innerRadius={innerRadius}
                    outerRadius={outerRadius}
                    startAngle={startAngle}
                    endAngle={endAngle}
                >

                    <PolarAngleAxis
                        type="number"
                        domain={[0, 100]}
                        tick={false}
                    />

                    {showTooltip && (
                        <Tooltip />
                    )}

                    <RadialBar
                        background
                        dataKey="value"
                        cornerRadius={12}
                    />

                    {(centerLabel || centerValue) && (

                        <>
                            {centerLabel && (

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
                                    y="58%"
                                    textAnchor="middle"
                                    fill="#F8FAFC"
                                    fontSize={28}
                                    fontWeight={700}
                                >
                                    {centerValue}
                                </Text>

                            )}
                        </>

                    )}

                </RadialBarChart>

            </ResponsiveContainer>

        </div>

    );

};

export default RadialChart;