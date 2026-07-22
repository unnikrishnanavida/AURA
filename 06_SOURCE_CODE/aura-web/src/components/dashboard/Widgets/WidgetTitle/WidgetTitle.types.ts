import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export interface WidgetTitleProps {
    title: ReactNode;
    description?: ReactNode;
    icon?: LucideIcon;
    badge?: ReactNode;
    className?: string;
}