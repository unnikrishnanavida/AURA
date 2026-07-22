import styles from "./ChartLegend.module.css";
import type { ChartLegendProps } from "./ChartLegend.types";

const ChartLegend = ({
    items,
    direction = "row",
    className = "",
}: ChartLegendProps) => {

    return (

        <div
            className={[
                styles.legend,
                styles[direction],
                className,
            ]
                .filter(Boolean)
                .join(" ")}
        >

            {items.map((item) => (

                <div
                    key={item.id}
                    className={styles.item}
                >

                    <span
                        className={styles.color}
                        style={{
                            backgroundColor: item.color,
                        }}
                    />

                    <span className={styles.label}>
                        {item.label}
                    </span>

                    {item.value !== undefined && (

                        <span className={styles.value}>
                            {item.value}
                        </span>

                    )}

                </div>

            ))}

        </div>

    );

};

export default ChartLegend;