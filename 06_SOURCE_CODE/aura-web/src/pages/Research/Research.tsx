import { useMemo, useState } from "react";
import { Download, BookOpen } from "lucide-react";

import styles from "./Research.module.css";

import type {
    ResearchItem,
    ResearchCategory,
    ResearchStatus,
} from "./Research.types";

const mockResearch: ResearchItem[] = [
    {
        id: "1",
        title: "Large Language Model Optimization",
        description:
            "Performance benchmarking and optimization of enterprise-scale language models for distributed environments.",
        category: "Artificial Intelligence",
        status: "completed",
        source: "OpenAI",
        author: "Research Team",
        confidence: 96,
        progress: 100,
        createdAt: "2026-07-10",
        updatedAt: "2026-07-15",
    },

    {
        id: "2",
        title: "Autonomous Agent Collaboration",
        description:
            "Study of multi-agent collaboration for autonomous software engineering systems.",
        category: "Machine Learning",
        status: "running",
        source: "Google DeepMind",
        author: "AURA AI",
        confidence: 91,
        progress: 72,
        createdAt: "2026-07-13",
        updatedAt: "2026-07-18",
    },

    {
        id: "3",
        title: "Cloud Security Analysis",
        description:
            "Security assessment of multi-cloud infrastructures with AI-powered threat detection.",
        category: "Cloud Computing",
        status: "queued",
        source: "Microsoft Research",
        author: "Cloud Team",
        confidence: 88,
        progress: 35,
        createdAt: "2026-07-18",
        updatedAt: "2026-07-19",
    },

    {
        id: "4",
        title: "Neural Code Generation",
        description:
            "Evaluation of code generation models across enterprise software development workflows.",
        category: "Software Engineering",
        status: "failed",
        source: "GitHub Research",
        author: "Development Team",
        confidence: 61,
        progress: 42,
        createdAt: "2026-07-16",
        updatedAt: "2026-07-19",
    },
];

const Research = () => {

    const [search, setSearch] = useState("");

    const [category, setCategory] = useState<
        ResearchCategory | "All"
    >("All");

    const [status, setStatus] = useState<
        ResearchStatus | "All"
    >("All");

    const filteredResearch = useMemo(() => {

        return mockResearch.filter((item) => {

            const matchesSearch =
                item.title.toLowerCase().includes(search.toLowerCase());

            const matchesCategory =
                category === "All" ||
                item.category === category;

            const matchesStatus =
                status === "All" ||
                item.status === status;

            return (
                matchesSearch &&
                matchesCategory &&
                matchesStatus
            );

        });

    }, [search, category, status]);

    const statistics = {

        total: mockResearch.length,

        completed: mockResearch.filter(
            x => x.status === "completed"
        ).length,

        running: mockResearch.filter(
            x => x.status === "running"
        ).length,

        queued: mockResearch.filter(
            x => x.status === "queued"
        ).length,

        failed: mockResearch.filter(
            x => x.status === "failed"
        ).length,

    };

    const getStatusClass = (
        status: ResearchStatus
    ) => {

        switch (status) {

            case "completed":
                return styles.completed;

            case "running":
                return styles.running;

            case "queued":
                return styles.queued;

            default:
                return styles.failed;

        }

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div className={styles.titleSection}>

                    <h1 className={styles.title}>
                        AI Research
                    </h1>

                    <p className={styles.subtitle}>
                        Explore, organize and monitor AI-generated research
                        across all enterprise knowledge sources.
                    </p>

                </div>

                <div className={styles.actions}>

                    <button className={styles.primaryButton}>

                        <Plus size={18} />

                        New Research

                    </button>

                </div>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <div className={styles.search}>

                    <input

                        className={styles.searchInput}

                        placeholder="Search research..."

                        value={search}

                        onChange={(e) =>
                            setSearch(e.target.value)
                        }

                    />

                </div>

                <div className={styles.filters}>

                    <select
                        className={styles.select}
                        value={category}
                        onChange={(e) =>
                            setCategory(
                                e.target.value as ResearchCategory | "All"
                            )
                        }
                    >

                        <option>All</option>
                        <option>Artificial Intelligence</option>
                        <option>Machine Learning</option>
                        <option>Cyber Security</option>
                        <option>Cloud Computing</option>
                        <option>Software Engineering</option>
                        <option>Data Science</option>

                    </select>

                    <select
                        className={styles.select}
                        value={status}
                        onChange={(e) =>
                            setStatus(
                                e.target.value as ResearchStatus | "All"
                            )
                        }
                    >

                        <option>All</option>
                        <option>completed</option>
                        <option>running</option>
                        <option>queued</option>
                        <option>failed</option>

                    </select>

                </div>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Total Research
                    </div>

                    <div className={styles.statValue}>
                        {statistics.total}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Completed
                    </div>

                    <div className={styles.statValue}>
                        {statistics.completed}
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
                        Queued
                    </div>

                    <div className={styles.statValue}>
                        {statistics.queued}
                    </div>

                </div>

            </section>
                        {/* ================= RESEARCH GRID ================= */}

            <section className={styles.grid}>

                {filteredResearch.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Research Found
                        </h3>

                        <p className={styles.description}>
                            No research matches your current search or filter
                            criteria.
                        </p>

                    </div>

                ) : (

                    filteredResearch.map((research) => (

                        <article
                            key={research.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div className={styles.cardHeader}>

                                <div>

                                    <h3 className={styles.cardTitle}>
                                        {research.title}
                                    </h3>

                                    <span className={styles.category}>
                                        {research.category}
                                    </span>

                                </div>

                                <span
                                    className={`${styles.status} ${getStatusClass(
                                        research.status
                                    )}`}
                                >
                                    {research.status.toUpperCase()}
                                </span>

                            </div>

                            {/* ---------- Description ---------- */}

                            <p className={styles.description}>
                                {research.description}
                            </p>

                            {/* ---------- Progress ---------- */}

                            <div>

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        marginBottom: 8,
                                        color: "#CBD5E1",
                                        fontSize: ".9rem",
                                    }}
                                >

                                    <span>Progress</span>

                                    <span>
                                        {research.progress}%
                                    </span>

                                </div>

                                <div className={styles.progress}>

                                    <div
                                        className={styles.progressFill}
                                        style={{
                                            width: `${research.progress}%`,
                                        }}
                                    />

                                </div>

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div className={styles.metaItem}>

                                    <span className={styles.metaLabel}>
                                        Source
                                    </span>

                                    <span className={styles.metaValue}>
                                        {research.source}
                                    </span>

                                </div>

                                <div className={styles.metaItem}>

                                    <span className={styles.metaLabel}>
                                        Author
                                    </span>

                                    <span className={styles.metaValue}>
                                        {research.author}
                                    </span>

                                </div>

                                <div className={styles.metaItem}>

                                    <span className={styles.metaLabel}>
                                        Confidence
                                    </span>

                                    <span className={styles.metaValue}>
                                        {research.confidence}%
                                    </span>

                                </div>

                                <div className={styles.metaItem}>

                                    <span className={styles.metaLabel}>
                                        Updated
                                    </span>

                                    <span className={styles.metaValue}>
                                        {research.updatedAt}
                                    </span>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    <BookOpen size={16} />

                                    Open
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    <Download size={16} />

                                    Export
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>
                    </main>

    );

};

export default Research;