import styles from "./Input.module.css";
import type { InputProps } from "./Input.types";

export default function Input({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  className = "",
  ...props
}: InputProps) {
  return (
    <div className={styles.container}>
      {label && (
        <label className={styles.label}>
          {label}
        </label>
      )}

      <div
        className={`${styles.inputWrapper} ${
          error ? styles.errorBorder : ""
        }`}
      >
        {leftIcon && (
          <span className={styles.icon}>
            {leftIcon}
          </span>
        )}

        <input
          className={`${styles.input} ${className}`}
          {...props}
        />

        {rightIcon && (
          <span className={styles.icon}>
            {rightIcon}
          </span>
        )}
      </div>

      {helperText && !error && (
        <small className={styles.helper}>
          {helperText}
        </small>
      )}

      {error && (
        <small className={styles.error}>
          {error}
        </small>
      )}
    </div>
  );
}