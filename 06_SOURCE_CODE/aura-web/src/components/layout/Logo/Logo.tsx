import styles from "./Logo.module.css";

export default function Logo() {
  return (
    <div className={styles.logo}>
      <div className={styles.icon}>A</div>

      <span>AURA</span>
    </div>
  );
}