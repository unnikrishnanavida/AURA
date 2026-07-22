import styles from "./WidgetContainer.module.css";
import type { WidgetContainerProps } from "./WidgetContainer.types";

const WidgetContainer = ({
    children,
    className = "",
    hoverable = true,
}: WidgetContainerProps) => {

    return (

        <section
            className={[
                styles.container,
                hoverable ? styles.hoverable : "",
                className,
            ]
                .filter(Boolean)
                .join(" ")}
        >
            {children}
        </section>

    );

};

export default WidgetContainer;