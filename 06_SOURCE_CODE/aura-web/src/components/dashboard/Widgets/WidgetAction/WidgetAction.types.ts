import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export type WidgetActionVariant =
    | "primary"
    | "secondary"
    | "ghost";

export interface WidgetActionProps
    extends ButtonHTMLAttributes<HTMLButtonElement> {

    children: ReactNode;

    icon?: LucideIcon;

    loading?: boolean;

    variant?: WidgetActionVariant;

    fullWidth?: boolean;
}