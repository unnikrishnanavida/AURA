import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import styles from "./KnowledgeBase.module.css";

import type {
    KnowledgeCategory,
    KnowledgeDocument,
    KnowledgeStatus,
} from "./KnowledgeBase.types";

const knowledgeData: KnowledgeDocument[] = [
    {
        id: "1",
        title: "Enterprise AI Architecture",
        description:
            "Complete documentation describing the AURA enterprise AI platform architecture, services, APIs, and deployment strategy.",
        category: "AI",
        status: "published",
        author: "Architecture Team",
        version: "v2.4",
        views: 1345,
        updatedAt: "2026-07-20",
        tags: ["architecture", "enterprise", "ai"],
    },
    {
        id: "2",
        title: "Cloud Deployment Guide",
        description:
            "Step-by-step deployment guide for Kubernetes, Docker, Azure, AWS, and Google Cloud.",
        category: "Cloud",
        status: "published",
        author: "DevOps Team",
        version: "v1.8",
        views: 842,
        updatedAt: "2026-07-18",
        tags: ["cloud", "docker", "kubernetes"],
    },
    {
        id: "3",
        title: "Security Standards",
        description:
            "Enterprise authentication, authorization, encryption, and zero-trust implementation guide.",
        category: "Security",
        status: "draft",
        author: "Security Team",
        version: "v0.9",
        views: 230,
        updatedAt: "2026-07-19",
        tags: ["security", "oauth", "jwt"],
    },
    {
        id: "4",
        title: "Research Documentation",
        description:
            "AI research reports, benchmark results, and model evaluation documentation.",
        category: "Research",
        status: "archived",
        author: "Research Division",
        version: "v1.2",
        views: 420,
        updatedAt: "2026-07-12",
        tags: ["research", "llm", "benchmark"],
    },
];

const KnowledgeBase = () => {

    const [search, setSearch] = useState("");

    const [category, setCategory] =
        useState<KnowledgeCategory | "All">("All");

    const [status, setStatus] =
        useState<KnowledgeStatus | "All">("All");

    const filteredDocuments = useMemo(() => {

        return knowledgeData.filter((document) => {

            const matchesSearch =
                document.title
                    .toLowerCase()
                    .includes(search.toLowerCase());

            const matchesCategory =
                category === "All" ||
                document.category === category;

            const matchesStatus =
                status === "All" ||
                document.status === status;

            return (
                matchesSearch &&
                matchesCategory &&
                matchesStatus
            );

        });

    }, [search, category, status]);

    const statistics = {

        total: knowledgeData.length,

        published: knowledgeData.filter(
            (d) => d.status === "published"
        ).length,

        drafts: knowledgeData.filter(
            (d) => d.status === "draft"
        ).length,

        archived: knowledgeData.filter(
            (d) => d.status === "archived"
        ).length,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        Knowledge Base
                    </h1>

                    <p className={styles.subtitle}>
                        Centralized enterprise documentation,
                        knowledge articles, research, and AI-powered
                        organizational intelligence.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Plus size={18} />

                    New Document

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <div className={styles.search}>

                    <input
                        className={styles.searchInput}
                        placeholder="Search knowledge..."
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                    />

                </div>

                <select
                    className={styles.select}
                    value={category}
                    onChange={(e) =>
                        setCategory(
                            e.target.value as
                                | KnowledgeCategory
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>AI</option>
                    <option>Cloud</option>
                    <option>Security</option>
                    <option>Programming</option>
                    <option>Research</option>
                    <option>Documentation</option>

                </select>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | KnowledgeStatus
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>published</option>
                    <option>draft</option>
                    <option>archived</option>

                </select>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Documents
                    </div>

                    <div className={styles.statValue}>
                        {statistics.total}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Published
                    </div>

                    <div className={styles.statValue}>
                        {statistics.published}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Drafts
                    </div>

                    <div className={styles.statValue}>
                        {statistics.drafts}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Archived
                    </div>

                    <div className={styles.statValue}>
                        {statistics.archived}
                    </div>

                </div>

            </section>
                        {/* ================= DOCUMENT GRID ================= */}

            <section className={styles.grid}>

                {filteredDocuments.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Documents Found
                        </h3>

                        <p className={styles.description}>
                            No knowledge documents match the current filters.
                        </p>

                    </div>

                ) : (

                    filteredDocuments.map((document) => (

                        <article
                            key={document.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div>

                                <h3 className={styles.cardTitle}>
                                    {document.title}
                                </h3>

                                <p className={styles.description}>
                                    {document.description}
                                </p>

                            </div>

                            {/* ---------- Tags ---------- */}

                            <div className={styles.tags}>

                                {document.tags.map((tag) => (

                                    <span
                                        key={tag}
                                        className={styles.tag}
                                    >
                                        #{tag}
                                    </span>

                                ))}

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Category
                                    </div>

                                    <div className={styles.metaValue}>
                                        {document.category}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {document.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Author
                                    </div>

                                    <div className={styles.metaValue}>
                                        {document.author}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Version
                                    </div>

                                    <div className={styles.metaValue}>
                                        {document.version}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Views
                                    </div>

                                    <div className={styles.metaValue}>
                                        {document.views.toLocaleString()}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Updated
                                    </div>

                                    <div className={styles.metaValue}>
                                        {document.updatedAt}
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    Open
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Edit
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default KnowledgeBase;