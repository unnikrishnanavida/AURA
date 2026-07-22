import styles from "./AIStatusCard.module.css";
import { BrainCircuit } from "lucide-react";
import type { AIStatusCardProps } from "./AIStatusCard.types";

const AIStatusCard = ({
  model,
  status,
  responseTime,
  metrics,
}: AIStatusCardProps) => {

  return (
    <section className={styles.card}>

      <div className={styles.header}>

        <div className={styles.titleSection}>

          <div className={styles.icon}>
            <BrainCircuit size={22} />
          </div>

          <div>

            <h3>AI Engine</h3>

            <p>{model}</p>

          </div>

        </div>

        <div
          className={`${styles.badge} ${styles[status]}`}
        >
          <span className={styles.dot}></span>
          {status}
        </div>

      </div>

      <div className={styles.response}>

        <span>Response Time</span>

        <strong>{responseTime}</strong>

      </div>

      <div className={styles.metrics}>

        {metrics.map((metric) => (

          <div
            key={metric.label}
            className={styles.metric}
          >

            <div className={styles.metricHeader}>

              <span>{metric.label}</span>

              <span>{metric.value}</span>

            </div>

            <div className={styles.progress}>

              <div
                className={`${styles.fill} ${styles[metric.color ?? "green"]}`}
                style={{
                  width: `${metric.percentage}%`,
                }}
              />

            </div>

          </div>

        ))}

      </div>

    </section>
  );
};

export default AIStatusCard;