import { useMemo, useState } from "react";
import { Play, Plus } from "lucide-react";

import styles from "./Automations.module.css";

import type {
    AutomationStatus,
    AutomationTrigger,
    AutomationWorkflow,
} from "./Automations.types";

const workflows: AutomationWorkflow[] = [
    {
        id: "1",
        name: "Daily Knowledge Sync",
        description:
            "Synchronizes enterprise knowledge base with AI vector storage every night.",
        trigger: "schedule",
        status: "running",
        owner: "AURA System",
        executions: 348,
        successRate: 99,
        lastRun: "Today 02:00 AM",
        nextRun: "Tomorrow 02:00 AM",
    },
    {
        id: "2",
        name: "Research Pipeline",
        description:
            "Automatically indexes research papers and generates semantic embeddings.",
        trigger: "event",
        status: "running",
        owner: "Research Team",
        executions: 128,
        successRate: 96,
        lastRun: "15 mins ago",
        nextRun: "On Upload",
    },
    {
        id: "3",
        name: "Security Audit",
        description:
            "Performs automated security scans and compliance validation.",
        trigger: "schedule",
        status: "paused",
        owner: "Security Team",
        executions: 82,
        successRate: 94,
        lastRun: "Yesterday",
        nextRun: "Paused",
    },
    {
        id: "4",
        name: "Webhook Integration",
        description:
            "Processes incoming webhook events from third-party services.",
        trigger: "webhook",
        status: "failed",
        owner: "Integration Team",
        executions: 54,
        successRate: 72,
        lastRun: "1 hour ago",
        nextRun: "--",
    },
];

const Automations = () => {

    const [search, setSearch] = useState("");

    const [trigger, setTrigger] =
        useState<AutomationTrigger | "All">("All");

    const [status, setStatus] =
        useState<AutomationStatus | "All">("All");

    const filteredWorkflows = useMemo(() => {

        return workflows.filter((workflow) => {

            const matchesSearch =
                workflow.name
                    .toLowerCase()
                    .includes(search.toLowerCase());

            const matchesTrigger =
                trigger === "All" ||
                workflow.trigger === trigger;

            const matchesStatus =
                status === "All" ||
                workflow.status === status;

            return (
                matchesSearch &&
                matchesTrigger &&
                matchesStatus
            );

        });

    }, [search, trigger, status]);

    const statistics = {

        total: workflows.length,

        running: workflows.filter(
            (workflow) => workflow.status === "running"
        ).length,

        paused: workflows.filter(
            (workflow) => workflow.status === "paused"
        ).length,

        failed: workflows.filter(
            (workflow) => workflow.status === "failed"
        ).length,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        AI Automations
                    </h1>

                    <p className={styles.subtitle}>
                        Build, schedule, monitor and manage enterprise AI workflows.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Plus size={18} />

                    New Automation

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <div className={styles.search}>

                    <input
                        className={styles.searchInput}
                        placeholder="Search workflows..."
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                    />

                </div>

                <select
                    className={styles.select}
                    value={trigger}
                    onChange={(e) =>
                        setTrigger(
                            e.target.value as
                                | AutomationTrigger
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>schedule</option>
                    <option>event</option>
                    <option>webhook</option>
                    <option>manual</option>

                </select>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | AutomationStatus
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>running</option>
                    <option>paused</option>
                    <option>stopped</option>
                    <option>failed</option>

                </select>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Total Workflows
                    </div>

                    <div className={styles.statValue}>
                        {statistics.total}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Running
                    </div>

                    <div className={styles.statValue}>
                        {statistics.running}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Paused
                    </div>

                    <div className={styles.statValue}>
                        {statistics.paused}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Failed
                    </div>

                    <div className={styles.statValue}>
                        {statistics.failed}
                    </div>

                </div>

            </section>
                        {/* ================= WORKFLOW GRID ================= */}

            <section className={styles.grid}>

                {filteredWorkflows.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Automations Found
                        </h3>

                        <p className={styles.description}>
                            No automation workflows match your current search
                            or filters.
                        </p>

                    </div>

                ) : (

                    filteredWorkflows.map((workflow) => (

                        <article
                            key={workflow.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div>

                                <h3 className={styles.cardTitle}>
                                    {workflow.name}
                                </h3>

                                <p className={styles.description}>
                                    {workflow.description}
                                </p>

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Trigger
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.trigger}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Owner
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.owner}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Executions
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.executions}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Success Rate
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.successRate}%
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Last Run
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.lastRun}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Next Run
                                    </div>

                                    <div className={styles.metaValue}>
                                        {workflow.nextRun}
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    <Play size={16} />

                                    Run
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Pause
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Stop
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default Automations;