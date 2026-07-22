import type {
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {

  children: ReactNode;

  variant?:
    | "primary"
    | "secondary"
    | "ghost"
    | "outline"
    | "danger"
    | "success";

  size?: "sm" | "md" | "lg";

  loading?: boolean;

  leftIcon?: ReactNode;

  rightIcon?: ReactNode;

  fullWidth?: boolean;
}