import { useMemo, useState } from "react";
import {
    Plus,
    Play,
    Square,
    RotateCcw,
    Settings,
} from "lucide-react";

import styles from "./Agents.module.css";
import type { Agent,
    AgentStatus,
 } from "./Agents.types";

const mockAgents: Agent[] = [
    {
        id: "1",
        name: "Research Agent",
        description: "AI Research Assistant",
        type: "research",
        model: "GPT-5.5",
        status: "online",
        cpuUsage: 18,
        memoryUsage: 2.1,
        tokenUsage: 65231,
        uptime: "5d 12h",
        tasksCompleted: 154,
        activeTasks: 4,
        responseTime: 284,
        lastSeen: "Now",
    },
    {
        id: "2",
        name: "Code Agent",
        description: "Software Engineer",
        type: "coding",
        model: "Claude 4",
        status: "busy",
        cpuUsage: 46,
        memoryUsage: 4.2,
        tokenUsage: 135621,
        uptime: "8d 6h",
        tasksCompleted: 431,
        activeTasks: 12,
        responseTime: 412,
        lastSeen: "Now",
    },
    {
        id: "3",
        name: "Vision Agent",
        description: "Image Processing",
        type: "vision",
        model: "Gemini Vision",
        status: "idle",
        cpuUsage: 8,
        memoryUsage: 1.4,
        tokenUsage: 18412,
        uptime: "2d 4h",
        tasksCompleted: 88,
        activeTasks: 1,
        responseTime: 178,
        lastSeen: "3 min ago",
    },
    {
        id: "4",
        name: "Security Agent",
        description: "Threat Detection",
        type: "security",
        model: "Llama 3",
        status: "offline",
        cpuUsage: 0,
        memoryUsage: 0,
        tokenUsage: 0,
        uptime: "--",
        tasksCompleted: 0,
        activeTasks: 0,
        responseTime: 0,
        lastSeen: "2 hrs ago",
    },
];

const Agents = () => {

    const [search, setSearch] = useState("");

    const filteredAgents = useMemo(() => {

        return mockAgents.filter((agent) =>
            agent.name.toLowerCase().includes(search.toLowerCase())
        );

    }, [search]);

    const stats = {

        total: mockAgents.length,

        online: mockAgents.filter(a => a.status === "online").length,

        busy: mockAgents.filter(a => a.status === "busy").length,

        idle: mockAgents.filter(a => a.status === "idle").length,

    };

    const getStatusClass = (status: AgentStatus) => {

        switch (status) {

            case "online":
                return styles.online;

            case "busy":
                return styles.busy;

            case "idle":
                return styles.idle;

            case "offline":
                return styles.offline;

            default:
                return styles.error;

        }

    };

    return (

        <main className={styles.page}>

            {/* Header */}

            <section className={styles.header}>

                <div className={styles.titleSection}>

                    <h1 className={styles.title}>
                        AI Agents
                    </h1>

                    <p className={styles.subtitle}>
                        Manage, monitor and control all AI agents running inside AURA.
                    </p>

                </div>

                <div className={styles.actions}>

                    <button className={styles.createButton}>

                        <Plus size={18} />

                        Create Agent

                    </button>

                </div>

            </section>

            {/* Search */}

            <section className={styles.toolbar}>

                <div className={styles.searchContainer}>

                    <input
                        className={styles.searchInput}
                        placeholder="Search agents..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />

                </div>

            </section>

            {/* Statistics */}

            <section className={styles.statsGrid}>

                <div className={styles.statCard}>

                    <div className={styles.statLabel}>Total Agents</div>

                    <div className={styles.statValue}>{stats.total}</div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statLabel}>Running</div>

                    <div className={styles.statValue}>{stats.online}</div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statLabel}>Busy</div>

                    <div className={styles.statValue}>{stats.busy}</div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statLabel}>Idle</div>

                    <div className={styles.statValue}>{stats.idle}</div>

                </div>

            </section>

            {/* Agents */}

            <section className={styles.agentGrid}>

                {

                    filteredAgents.map(agent => (

                        <article
                            key={agent.id}
                            className={styles.agentCard}
                        >

                            <div className={styles.agentHeader}>

                                <div>

                                    <div className={styles.agentName}>
                                        {agent.name}
                                    </div>

                                    <div className={styles.agentModel}>
                                        {agent.model}
                                    </div>

                                </div>

                                <span
                                    className={`${styles.status} ${getStatusClass(agent.status)}`}
                                >
                                    {agent.status}
                                </span>

                            </div>

                            <div className={styles.metrics}>

                                <div className={styles.metric}>
                                    <span className={styles.metricLabel}>CPU</span>
                                    <span className={styles.metricValue}>{agent.cpuUsage}%</span>
                                </div>

                                <div className={styles.metric}>
                                    <span className={styles.metricLabel}>RAM</span>
                                    <span className={styles.metricValue}>{agent.memoryUsage} GB</span>
                                </div>

                                <div className={styles.metric}>
                                    <span className={styles.metricLabel}>Tasks</span>
                                    <span className={styles.metricValue}>{agent.tasksCompleted}</span>
                                </div>

                                <div className={styles.metric}>
                                    <span className={styles.metricLabel}>Response</span>
                                    <span className={styles.metricValue}>{agent.responseTime} ms</span>
                                </div>

                            </div>

                            <div className={styles.cardFooter}>

                                <div className={styles.buttonGroup}>

                                    <button className={styles.iconButton}>
                                        <Play size={16} />
                                    </button>

                                    <button className={styles.iconButton}>
                                        <Square size={16} />
                                    </button>

                                    <button className={styles.iconButton}>
                                        <RotateCcw size={16} />
                                    </button>

                                    <button className={styles.iconButton}>
                                        <Settings size={16} />
                                    </button>

                                </div>

                                <span className={styles.lastSeen}>
                                    {agent.lastSeen}
                                </span>

                            </div>

                        </article>

                    ))

                }

            </section>

        </main>

    );

};

export default Agents;