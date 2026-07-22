import styles from "./AgentList.module.css";
import {
    ArrowUpRight,
    Cpu,
} from "lucide-react";

import type {
    AgentListProps,
} from "./AgentList.types";

const AgentList = ({
    agents,
    onOpen,
}: AgentListProps) => {

    return (

        <section className={styles.card}>

            <div className={styles.header}>

                <h2>AI Agents</h2>

                <span>{agents.length} Active</span>

            </div>

            <div className={styles.list}>

                {agents.map((agent) => {

                    const Icon = agent.icon;

                    return (

                        <div
                            key={agent.id}
                            className={styles.agent}
                        >

                            <div className={styles.left}>

                                <div className={styles.icon}>
                                    <Icon size={22} />
                                </div>

                                <div>

                                    <h3>{agent.name}</h3>

                                    <p>{agent.description}</p>

                                    <span
                                        className={`${styles.status} ${styles[agent.status]}`}
                                    >
                                        {agent.status}
                                    </span>

                                </div>

                            </div>

                            <div className={styles.center}>

                                <span className={styles.task}>
                                    {agent.task}
                                </span>

                                <div className={styles.usage}>

                                    <Cpu size={15} />

                                    {agent.usage}%

                                </div>

                                <div className={styles.progress}>

                                    <div
                                        className={styles.fill}
                                        style={{
                                            width: `${agent.usage}%`,
                                        }}
                                    />

                                </div>

                                <small>
                                    Last Active {agent.lastActive}
                                </small>

                            </div>

                            {onOpen && (

                                <button
                                    type="button"
                                    className={styles.button}
                                    onClick={() => onOpen(agent.id)}
                                >

                                    Open

                                    <ArrowUpRight size={17} />

                                </button>

                            )}

                        </div>

                    );

                })}

            </div>

        </section>

    );

};

export default AgentList;