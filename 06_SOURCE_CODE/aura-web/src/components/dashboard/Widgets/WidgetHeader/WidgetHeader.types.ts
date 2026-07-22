import type { ReactNode } from "react";

export interface WidgetHeaderProps {
    title: ReactNode;
    subtitle?: ReactNode;
    action?: ReactNode;
    className?: string;
}