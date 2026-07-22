import styles from "./GlassCard.module.css";
import type { GlassCardProps } from "./GlassCard.types";

export default function GlassCard({
  children,
  blur = "md",
  padding = "md",
  hover = true,
  className = "",
  ...props
}: GlassCardProps) {
  return (
    <div
      className={[
        styles.card,
        styles[blur],
        styles[padding],
        hover ? styles.hover : "",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}