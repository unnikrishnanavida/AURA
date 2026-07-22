import {
    Activity,
    BrainCircuit,
    Cpu,
    GitBranch,
    Network,
    Sparkles,
} from "lucide-react";

import styles from "./Brain.module.css";

import type {
    AgentMemory,
    BrainProps,
    CognitiveMetric,
    MemoryNode,
} from "./Brain.types";

const metrics: CognitiveMetric[] = [
    {
        label: "Neural Connections",
        value: "24,582",
        change: "+8.4%",
    },
    {
        label: "Memory Tokens",
        value: "18.6M",
        change: "+2.1%",
    },
    {
        label: "Reasoning Accuracy",
        value: "98.9%",
        change: "+0.4%",
    },
    {
        label: "Active Agents",
        value: "128",
        change: "+16",
    },
];

const memoryNodes: MemoryNode[] = [
    {
        id: "1",
        title: "Enterprise Knowledge",
        type: "Long-Term Memory",
        status: "active",
        connections: 328,
    },
    {
        id: "2",
        title: "Conversation Context",
        type: "Working Memory",
        status: "processing",
        connections: 144,
    },
    {
        id: "3",
        title: "Research Repository",
        type: "Knowledge Graph",
        status: "active",
        connections: 492,
    },
    {
        id: "4",
        title: "Agent Experiences",
        type: "Semantic Memory",
        status: "idle",
        connections: 211,
    },
];

const activeMemories: AgentMemory[] = [
    {
        id: "1",
        agent: "Research Agent",
        context: "Analyzing enterprise AI adoption patterns.",
        tokens: 14281,
    },
    {
        id: "2",
        agent: "Analytics Agent",
        context: "Building predictive usage insights.",
        tokens: 8632,
    },
    {
        id: "3",
        agent: "Automation Agent",
        context: "Optimizing workflow execution pipeline.",
        tokens: 11754,
    },
];

const Brain = ({
    className,
}: BrainProps) => {

    return (

        <main
            className={`${styles.page} ${className ?? ""}`}
        >

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div className={styles.titleGroup}>

                    <h1 className={styles.title}>
                        AI Brain
                    </h1>

                    <p className={styles.subtitle}>
                        Monitor neural cognition,
                        contextual memory and
                        enterprise intelligence.
                    </p>

                </div>

                <BrainCircuit
                    size={52}
                    color="#D4AF37"
                />

            </header>

            {/* ================= METRICS ================= */}

            <section className={styles.metrics}>

                {metrics.map((metric) => (

                    <article
                        key={metric.label}
                        className={styles.metricCard}
                    >

                        <div className={styles.metricValue}>
                            {metric.value}
                        </div>

                        <div className={styles.metricLabel}>
                            {metric.label}
                        </div>

                        <div className={styles.metricChange}>
                            {metric.change}
                        </div>

                    </article>

                ))}

            </section>

            {/* ================= MAIN LAYOUT ================= */}

            <section className={styles.layout}>

                {/* ================= MEMORY GRAPH ================= */}

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Neural Memory Network
                    </h2>

                    <div className={styles.nodeGrid}>

                        {memoryNodes.map((node) => (

                            <article
                                key={node.id}
                                className={styles.node}
                            >

                                <Network
                                    size={30}
                                    color="#D4AF37"
                                />

                                <div
                                    className={
                                        styles.nodeTitle
                                    }
                                >
                                    {node.title}
                                </div>

                                <div
                                    className={
                                        styles.nodeType
                                    }
                                >
                                    {node.type}
                                </div>

                                <div
                                    className={
                                        styles.status
                                    }
                                >
                                    {node.status}
                                </div>

                                <div
                                    className={
                                        styles.connections
                                    }
                                >
                                    Connections:
                                    {" "}
                                    {node.connections}
                                </div>

                            </article>

                        ))}

                    </div>

                </section>

                {/* ================= ACTIVE MEMORY ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Active Context
                    </h2>

                    <div className={styles.memoryList}>

                        {activeMemories.map((memory) => (

                            <article
                                key={memory.id}
                                className={
                                    styles.memoryCard
                                }
                            >

                                <div
                                    className={styles.agent}
                                >
                                    {memory.agent}
                                </div>

                                <div
                                    className={
                                        styles.context
                                    }
                                >
                                    {memory.context}
                                </div>

                                <div
                                    className={
                                        styles.tokens
                                    }
                                >
                                    Tokens:
                                    {" "}
                                    {memory.tokens.toLocaleString()}
                                </div>

                            </article>

                        ))}

                    </div>

                </aside>

            </section>
                        {/* ================= COGNITIVE PIPELINE ================= */}

            <section className={styles.layout}>

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Cognitive Processing Pipeline
                    </h2>

                    <div className={styles.memoryList}>

                        {[
                            {
                                stage: "Input Processing",
                                status: "Completed",
                                icon: <Activity size={20} color="#22C55E" />,
                            },
                            {
                                stage: "Semantic Analysis",
                                status: "Running",
                                icon: <BrainCircuit size={20} color="#D4AF37" />,
                            },
                            {
                                stage: "Knowledge Retrieval",
                                status: "Running",
                                icon: <GitBranch size={20} color="#3B82F6" />,
                            },
                            {
                                stage: "Reasoning Engine",
                                status: "Optimizing",
                                icon: <Cpu size={20} color="#A855F7" />,
                            },
                            {
                                stage: "Response Generation",
                                status: "Queued",
                                icon: <Sparkles size={20} color="#F97316" />,
                            },
                        ].map((item) => (

                            <article
                                key={item.stage}
                                className={styles.memoryCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                    }}
                                >

                                    <div
                                        style={{
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 14,
                                        }}
                                    >

                                        {item.icon}

                                        <div>

                                            <div
                                                className={styles.agent}
                                            >
                                                {item.stage}
                                            </div>

                                            <div
                                                className={styles.context}
                                            >
                                                {item.status}
                                            </div>

                                        </div>

                                    </div>

                                    <span
                                        className={styles.status}
                                    >
                                        Live
                                    </span>

                                </div>

                            </article>

                        ))}

                    </div>

                </section>

                {/* ================= SYSTEM HEALTH ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Brain Health
                    </h2>

                    <div className={styles.memoryList}>

                        {[
                            {
                                label: "Reasoning Engine",
                                value: "99.8%",
                            },
                            {
                                label: "Knowledge Accuracy",
                                value: "98.9%",
                            },
                            {
                                label: "Memory Consistency",
                                value: "99.4%",
                            },
                            {
                                label: "Context Retention",
                                value: "97.8%",
                            },
                            {
                                label: "Inference Speed",
                                value: "34 ms",
                            },
                        ].map((metric) => (

                            <div
                                key={metric.label}
                                className={styles.memoryCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                    }}
                                >

                                    <span>
                                        {metric.label}
                                    </span>

                                    <strong
                                        style={{
                                            color: "#D4AF37",
                                        }}
                                    >
                                        {metric.value}
                                    </strong>

                                </div>

                            </div>

                        ))}

                    </div>

                </aside>

            </section>

            {/* ================= AGENT SYNCHRONIZATION ================= */}

            <section className={styles.panel}>

                <h2 className={styles.panelTitle}>
                    Agent Synchronization
                </h2>

                <div className={styles.nodeGrid}>

                    {[
                        "Research Agent",
                        "Analytics Agent",
                        "Automation Agent",
                        "Security Agent",
                        "Knowledge Agent",
                        "Cloud Agent",
                        "Monitoring Agent",
                        "Coding Agent",
                    ].map((agent) => (

                        <article
                            key={agent}
                            className={styles.node}
                        >

                            <Cpu
                                size={30}
                                color="#D4AF37"
                            />

                            <div className={styles.nodeTitle}>
                                {agent}
                            </div>

                            <div className={styles.nodeType}>
                                Connected to AI Brain
                            </div>

                            <div className={styles.status}>
                                Synchronized
                            </div>

                        </article>

                    ))}

                </div>

            </section>

        </main>

    );

};

export default Brain;