import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import styles from "./Evolution.module.css";

import type {
    BenchmarkType,
    EvolutionStatus,
    ModelEvolution,
} from "./Evolution.types";

const versions: ModelEvolution[] = [
    {
        id: "1",
        version: "v1.0",
        title: "Foundation Model",
        description:
            "Initial enterprise language model with core reasoning capabilities.",
        releaseDate: "2026-01-15",
        status: "Released",
        benchmark: "Accuracy",
        score: 86,
        improvement: 0,
    },
    {
        id: "2",
        version: "v2.0",
        title: "Reasoning Upgrade",
        description:
            "Enhanced multi-step reasoning, planning and instruction following.",
        releaseDate: "2026-03-10",
        status: "Released",
        benchmark: "Reasoning",
        score: 92,
        improvement: 6,
    },
    {
        id: "3",
        version: "v3.0",
        title: "Coding Intelligence",
        description:
            "Improved software engineering, debugging and code generation.",
        releaseDate: "2026-05-20",
        status: "Testing",
        benchmark: "Coding",
        score: 95,
        improvement: 3,
    },
    {
        id: "4",
        version: "v4.0",
        title: "Multimodal AI",
        description:
            "Image understanding, OCR and document intelligence.",
        releaseDate: "2026-08-01",
        status: "Training",
        benchmark: "Multimodal",
        score: 89,
        improvement: 8,
    },
    {
        id: "5",
        version: "v5.0",
        title: "Autonomous Agent",
        description:
            "Advanced enterprise agent orchestration and workflow automation.",
        releaseDate: "2026-12-15",
        status: "Planning",
        benchmark: "Reasoning",
        score: 0,
        improvement: 0,
    },
];

const Evolution = () => {

    const [status, setStatus] =
        useState<EvolutionStatus | "All">("All");

    const [benchmark, setBenchmark] =
        useState<BenchmarkType | "All">("All");

    const filteredVersions = useMemo(() => {

        return versions.filter((version) => {

            const matchesStatus =
                status === "All" ||
                version.status === status;

            const matchesBenchmark =
                benchmark === "All" ||
                version.benchmark === benchmark;

            return (
                matchesStatus &&
                matchesBenchmark
            );

        });

    }, [status, benchmark]);

    const statistics = {

        totalVersions: versions.length,

        activeVersions: versions.filter(
            (version) =>
                version.status === "Released"
        ).length,

        experiments: 48,

        benchmarks: 126,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        AI Evolution
                    </h1>

                    <p className={styles.subtitle}>
                        Monitor model evolution, benchmark improvements,
                        releases and future roadmap.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Plus size={18} />

                    New Experiment

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | EvolutionStatus
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>Planning</option>
                    <option>Training</option>
                    <option>Testing</option>
                    <option>Released</option>
                    <option>Deprecated</option>

                </select>

                <select
                    className={styles.select}
                    value={benchmark}
                    onChange={(e) =>
                        setBenchmark(
                            e.target.value as
                                | BenchmarkType
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>Accuracy</option>
                    <option>Latency</option>
                    <option>Reasoning</option>
                    <option>Coding</option>
                    <option>Multimodal</option>

                </select>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Versions
                    </div>

                    <div className={styles.statValue}>
                        {statistics.totalVersions}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Released
                    </div>

                    <div className={styles.statValue}>
                        {statistics.activeVersions}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Experiments
                    </div>

                    <div className={styles.statValue}>
                        {statistics.experiments}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Benchmarks
                    </div>

                    <div className={styles.statValue}>
                        {statistics.benchmarks}
                    </div>

                </div>

            </section>
                        {/* ================= EVOLUTION GRID ================= */}

            <section className={styles.grid}>

                {filteredVersions.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Versions Found
                        </h3>

                        <p className={styles.description}>
                            No AI model versions match the selected filters.
                        </p>

                    </div>

                ) : (

                    filteredVersions.map((version) => (

                        <article
                            key={version.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div>

                                <h3 className={styles.cardTitle}>
                                    {version.title}
                                </h3>

                                <p className={styles.description}>
                                    {version.version}
                                </p>

                            </div>

                            {/* ---------- Description ---------- */}

                            <p className={styles.description}>
                                {version.description}
                            </p>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {version.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Benchmark
                                    </div>

                                    <div className={styles.metaValue}>
                                        {version.benchmark}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Score
                                    </div>

                                    <div className={styles.metaValue}>
                                        {version.score}%
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Improvement
                                    </div>

                                    <div className={styles.metaValue}>
                                        +{version.improvement}%
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Release Date
                                    </div>

                                    <div className={styles.metaValue}>
                                        {version.releaseDate}
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    View Details
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Compare
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Run Benchmark
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default Evolution;