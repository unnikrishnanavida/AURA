import styles from "./TokenUsage.module.css";
import { Coins, Wallet, DollarSign } from "lucide-react";
import type { TokenUsageProps } from "./TokenUsage.types";

const TokenUsage = ({
    totalTokens,
    usedTokens,
    remainingTokens,
    estimatedCost,
    period = "This Month",
}: TokenUsageProps) => {

    const percentage = Math.min(
        (usedTokens / totalTokens) * 100,
        100
    );

    return (
        <section className={styles.card}>

            <div className={styles.header}>

                <div>

                    <h2>Token Usage</h2>

                    <span>{period}</span>

                </div>

                <Coins size={28} />

            </div>

            <div className={styles.progressSection}>

                <div className={styles.progress}>

                    <div
                        className={styles.fill}
                        style={{
                            width: `${percentage}%`,
                        }}
                    />

                </div>

                <span>
                    {percentage.toFixed(1)}%
                </span>

            </div>

            <div className={styles.stats}>

                <div className={styles.stat}>

                    <Wallet size={18} />

                    <div>

                        <small>Used</small>

                        <strong>
                            {usedTokens.toLocaleString()}
                        </strong>

                    </div>

                </div>

                <div className={styles.stat}>

                    <Coins size={18} />

                    <div>

                        <small>Remaining</small>

                        <strong>
                            {remainingTokens.toLocaleString()}
                        </strong>

                    </div>

                </div>

                <div className={styles.stat}>

                    <DollarSign size={18} />

                    <div>

                        <small>Estimated Cost</small>

                        <strong>{estimatedCost}</strong>

                    </div>

                </div>

            </div>

        </section>
    );
};

export default TokenUsage;