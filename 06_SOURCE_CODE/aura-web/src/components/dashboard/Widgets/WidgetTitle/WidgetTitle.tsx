import styles from "./WidgetTitle.module.css";
import type { WidgetTitleProps } from "./WidgetTitle.types";

const WidgetTitle = ({
    title,
    description,
    icon: Icon,
    badge,
    className = "",
}: WidgetTitleProps) => {

    return (

        <div
            className={[
                styles.container,
                className,
            ]
                .filter(Boolean)
                .join(" ")}
        >

            {Icon && (

                <div className={styles.icon}>

                    <Icon size={22} />

                </div>

            )}

            <div className={styles.content}>

                <div className={styles.row}>

                    <h2 className={styles.title}>
                        {title}
                    </h2>

                    {badge}

                </div>

                {description && (

                    <p className={styles.description}>
                        {description}
                    </p>

                )}

            </div>

        </div>

    );

};

export default WidgetTitle;