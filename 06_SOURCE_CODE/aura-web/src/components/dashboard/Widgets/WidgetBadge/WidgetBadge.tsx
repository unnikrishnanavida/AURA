import styles from "./WidgetBadge.module.css";
import type { WidgetBadgeProps } from "./WidgetBadge.types";

const WidgetBadge = ({
    children,
    variant = "primary",
    outlined = false,
    className = "",
}: WidgetBadgeProps) => {

    return (

        <span
            className={[
                styles.badge,
                styles[variant],
                outlined ? styles.outlined : "",
                className,
            ]
                .filter(Boolean)
                .join(" ")}
        >
            {children}
        </span>

    );

};

export default WidgetBadge;