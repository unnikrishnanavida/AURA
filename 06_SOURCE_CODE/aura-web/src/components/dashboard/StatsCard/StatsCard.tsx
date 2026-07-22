import styles from "./StatsCard.module.css";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import type { StatsCardProps } from "./StatsCard.types";

const StatsCard = ({
    title,
    value,
    icon: Icon,
    trend,
    trendValue,
    subtitle,
    onClick
}: StatsCardProps) => {

    const TrendIcon =
        trend === "up"
            ? ArrowUpRight
            : trend === "down"
            ? ArrowDownRight
            : ArrowRight;

    return (
        <div
            className={styles.card}
            onClick={onClick}
        >
            <div className={styles.header}>

                <div className={styles.iconContainer}>
                    <Icon size={22} />
                </div>

                <div
                    className={`${styles.trend} ${styles[trend]}`}
                >
                    <TrendIcon size={16} />
                    <span>{trendValue}</span>
                </div>

            </div>

            <div className={styles.content}>

                <h4 className={styles.title}>
                    {title}
                </h4>

                <h2 className={styles.value}>
                    {value}
                </h2>

                {subtitle && (
                    <p className={styles.subtitle}>
                        {subtitle}
                    </p>
                )}

            </div>
        </div>
    );
};

export default StatsCard;