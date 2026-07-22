import styles from "./WidgetHeader.module.css";
import type { WidgetHeaderProps } from "./WidgetHeader.types";

const WidgetHeader = ({
    title,
    subtitle,
    action,
    className = "",
}: WidgetHeaderProps) => {

    return (

        <header
            className={[
                styles.header,
                className,
            ]
                .filter(Boolean)
                .join(" ")}
        >

            <div className={styles.content}>

                <div className={styles.text}>

                    <h2 className={styles.title}>
                        {title}
                    </h2>

                    {subtitle && (
                        <p className={styles.subtitle}>
                            {subtitle}
                        </p>
                    )}

                </div>

            </div>

            {action && (
                <div className={styles.action}>
                    {action}
                </div>
            )}

        </header>

    );

};

export default WidgetHeader;