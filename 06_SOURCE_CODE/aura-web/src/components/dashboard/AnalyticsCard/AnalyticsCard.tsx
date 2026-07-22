import styles from "./AnalyticsCard.module.css";
import type { AnalyticsCardProps } from "./AnalyticsCard.types";
import {
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronRight,
} from "lucide-react";

const AnalyticsCard = ({
    title = "Analytics Overview",
    metrics,
    onViewReport,
}: AnalyticsCardProps) => {

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case "up":
                return <TrendingUp size={16} />;
            case "down":
                return <TrendingDown size={16} />;
            default:
                return <Minus size={16} />;
        }
    };

    return (
        <section className={styles.card}>

            <div className={styles.header}>

                <h2>{title}</h2>

                {onViewReport && (
                    <button
                        type="button"
                        className={styles.button}
                        onClick={onViewReport}
                    >
                        View Report
                        <ChevronRight size={17} />
                    </button>
                )}

            </div>

            <div className={styles.grid}>

                {metrics.map((metric) => {

                    const Icon = metric.icon;

                    return (

                        <div
                            key={metric.id}
                            className={styles.metric}
                        >

                            <div className={styles.icon}>
                                <Icon size={22} />
                            </div>

                            <h4>{metric.title}</h4>

                            <h3>{metric.value}</h3>

                            <div
                                className={`${styles.trend} ${styles[metric.trend]}`}
                            >

                                {getTrendIcon(metric.trend)}

                                <span>{metric.change}</span>

                            </div>

                        </div>

                    );

                })}

            </div>

        </section>
    );
};

export default AnalyticsCard;