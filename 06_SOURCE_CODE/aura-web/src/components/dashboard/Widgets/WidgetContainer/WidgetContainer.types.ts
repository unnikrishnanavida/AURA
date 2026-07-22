import type { ReactNode } from "react";

export interface WidgetContainerProps {
    children: ReactNode;
    className?: string;
    hoverable?: boolean;
}