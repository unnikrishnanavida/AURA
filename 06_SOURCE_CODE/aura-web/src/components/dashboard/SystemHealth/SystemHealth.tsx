import styles from "./SystemHealth.module.css";
import {
    Cpu,
    HardDrive,
    Database,
    Server,
} from "lucide-react";

import type {
    SystemHealthProps,
} from "./SystemHealth.types";

const icons = [
    Cpu,
    HardDrive,
    Database,
    Server,
];

const SystemHealth = ({
    metrics,
}: SystemHealthProps) => {

    return (

        <section className={styles.card}>

            <div className={styles.header}>

                <h2>System Health</h2>

                <span>
                    {metrics.length} Services
                </span>

            </div>

            <div className={styles.list}>

                {metrics.map((metric, index) => {

                    const Icon =
                        icons[index % icons.length];

                    return (

                        <div
                            key={metric.id}
                            className={styles.item}
                        >

                            <div className={styles.left}>

                                <div className={styles.icon}>
                                    <Icon size={20} />
                                </div>

                                <div>

                                    <h4>{metric.name}</h4>

                                    <span>
                                        {metric.value}
                                    </span>

                                </div>

                            </div>

                            <div className={styles.right}>

                                <span
                                    className={`${styles.status} ${styles[metric.status]}`}
                                >
                                    {metric.status}
                                </span>

                                <div className={styles.progress}>

                                    <div
                                        className={styles.fill}
                                        style={{
                                            width: `${metric.usage}%`,
                                        }}
                                    />

                                </div>

                            </div>

                        </div>

                    );

                })}

            </div>

        </section>

    );

};

export default SystemHealth;