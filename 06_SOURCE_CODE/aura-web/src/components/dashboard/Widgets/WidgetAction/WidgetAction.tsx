import styles from "./WidgetAction.module.css";
import { Loader2 } from "lucide-react";
import type { WidgetActionProps } from "./WidgetAction.types";

const WidgetAction = ({
    children,
    icon: Icon,
    loading = false,
    disabled,
    variant = "primary",
    fullWidth = false,
    className = "",
    ...props
}: WidgetActionProps) => {

    return (

        <button
            type="button"
            disabled={disabled || loading}
            className={[
                styles.button,
                styles[variant],
                fullWidth ? styles.fullWidth : "",
                className,
            ]
                .filter(Boolean)
                .join(" ")}
            {...props}
        >

            {loading ? (

                <Loader2
                    size={18}
                    className={styles.spinner}
                />

            ) : (

                Icon && <Icon size={18} />

            )}

            <span>{children}</span>

        </button>

    );

};

export default WidgetAction;