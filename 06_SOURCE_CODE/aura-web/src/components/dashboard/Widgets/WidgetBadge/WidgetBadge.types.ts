import type { ReactNode } from "react";

export type WidgetBadgeVariant =
    | "primary"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "neutral";

export interface WidgetBadgeProps {
    children: ReactNode;
    variant?: WidgetBadgeVariant;
    outlined?: boolean;
    className?: string;
}