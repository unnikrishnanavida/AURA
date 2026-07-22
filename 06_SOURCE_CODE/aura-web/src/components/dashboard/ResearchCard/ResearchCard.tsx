import styles from "./ResearchCard.module.css";
import {
  FileText,
  BrainCircuit,
  ArrowUpRight,
} from "lucide-react";
import type { ResearchCardProps } from "./ResearchCard.types";

const ResearchCard = ({
  title,
  source,
  description,
  confidence,
  status,
  updatedAt,
  onOpen,
}: ResearchCardProps) => {
  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <div className={styles.icon}>
          <BrainCircuit size={22} />
        </div>

        <span
          className={`${styles.status} ${styles[status]}`}
        >
          {status}
        </span>
      </div>

      <h3>{title}</h3>

      <div className={styles.source}>
        <FileText size={16} />
        <span>{source}</span>
      </div>

      <p>{description}</p>

      <div className={styles.confidenceSection}>
        <div className={styles.row}>
          <span>Confidence</span>
          <strong>{confidence}%</strong>
        </div>

        <div className={styles.progress}>
          <div
            className={styles.fill}
            style={{
              width: `${confidence}%`,
            }}
          />
        </div>
      </div>

      <div className={styles.footer}>
        <small>{updatedAt}</small>

        {onOpen && (
          <button
            type="button"
            className={styles.openButton}
            onClick={onOpen}
          >
            Open
            <ArrowUpRight size={16} />
          </button>
        )}
      </div>
    </section>
  );
};

export default ResearchCard;