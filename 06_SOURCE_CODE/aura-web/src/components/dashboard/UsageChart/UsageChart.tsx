import styles from "./UsageChart.module.css";
import {
    ChevronRight,
    TrendingUp,
} from "lucide-react";
import type { UsageChartProps } from "./UsageChart.types";

const UsageChart = ({
    title = "Usage Analytics",
    subtitle = "AI usage over time",
    chart,
    data,
    onViewAnalytics,
}: UsageChartProps) => {

    const total = data.reduce(
        (sum, item) => sum + item.value,
        0
    );

    const average =
        data.length > 0
            ? Math.round(total / data.length)
            : 0;

    return (

        <section className={styles.card}>

            <div className={styles.header}>

                <div>

                    <h2>{title}</h2>

                    <p>{subtitle}</p>

                </div>

                {onViewAnalytics && (

                    <button
                        type="button"
                        className={styles.button}
                        onClick={onViewAnalytics}
                    >

                        View Analytics

                        <ChevronRight size={17} />

                    </button>

                )}

            </div>

            <div className={styles.chartContainer}>

                {chart}

            </div>

            <div className={styles.footer}>

                <div className={styles.metric}>

                    <TrendingUp size={18} />

                    <div>

                        <small>Total Usage</small>

                        <strong>{total}</strong>

                    </div>

                </div>

                <div className={styles.metric}>

                    <TrendingUp size={18} />

                    <div>

                        <small>Average</small>

                        <strong>{average}</strong>

                    </div>

                </div>

                <div className={styles.metric}>

                    <TrendingUp size={18} />

                    <div>

                        <small>Data Points</small>

                        <strong>{data.length}</strong>

                    </div>

                </div>

            </div>

        </section>

    );

};

export default UsageChart;