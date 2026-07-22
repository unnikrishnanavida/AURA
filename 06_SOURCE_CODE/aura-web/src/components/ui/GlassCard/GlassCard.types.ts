import type { HTMLAttributes, ReactNode } from "react";

export interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;

  blur?: "sm" | "md" | "lg";

  padding?: "none" | "sm" | "md" | "lg";

  hover?: boolean;
}
