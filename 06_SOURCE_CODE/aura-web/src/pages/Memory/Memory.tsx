import { useMemo, useState } from "react";

import styles from "./Memory.module.css";

import type {
    MemoryItem,
    MemoryStatus,
    MemoryType,
} from "./Memory.types";

const memoryData: MemoryItem[] = [
    {
        id: "1",
        title: "User Coding Preference",
        description:
            "The user prefers complete production-ready code instead of snippets.",
        type: "preference",
        status: "active",
        confidence: 99,
        importance: 98,
        createdAt: "2026-07-10",
        updatedAt: "2026-07-20",
        source: "Conversation",
        tags: ["coding", "preferences"],
    },
    {
        id: "2",
        title: "Enterprise Dashboard",
        description:
            "AURA dashboard architecture and reusable enterprise components.",
        type: "knowledge",
        status: "active",
        confidence: 97,
        importance: 94,
        createdAt: "2026-07-12",
        updatedAt: "2026-07-20",
        source: "Workspace",
        tags: ["dashboard", "architecture"],
    },
    {
        id: "3",
        title: "Chat UI",
        description:
            "Enterprise AI chat interface with conversation history.",
        type: "code",
        status: "archived",
        confidence: 93,
        importance: 86,
        createdAt: "2026-07-15",
        updatedAt: "2026-07-18",
        source: "Git Repository",
        tags: ["react", "typescript"],
    },
    {
        id: "4",
        title: "Research Summary",
        description:
            "AI generated enterprise research and semantic indexing.",
        type: "document",
        status: "expired",
        confidence: 81,
        importance: 74,
        createdAt: "2026-07-01",
        updatedAt: "2026-07-08",
        source: "Research Module",
        tags: ["research", "ai"],
    },
];

const Memory = () => {

    const [search, setSearch] = useState("");

    const [type, setType] =
        useState<MemoryType | "All">("All");

    const [status, setStatus] =
        useState<MemoryStatus | "All">("All");

    const filteredMemory = useMemo(() => {

        return memoryData.filter((item) => {

            const matchesSearch =
                item.title
                    .toLowerCase()
                    .includes(search.toLowerCase());

            const matchesType =
                type === "All" || item.type === type;

            const matchesStatus =
                status === "All" ||
                item.status === status;

            return (
                matchesSearch &&
                matchesType &&
                matchesStatus
            );

        });

    }, [search, type, status]);

    const statistics = {

        total: memoryData.length,

        active: memoryData.filter(
            (m) => m.status === "active"
        ).length,

        archived: memoryData.filter(
            (m) => m.status === "archived"
        ).length,

        expired: memoryData.filter(
            (m) => m.status === "expired"
        ).length,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        AI Memory
                    </h1>

                    <p className={styles.subtitle}>
                        Long-term semantic memory and
                        enterprise knowledge storage.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Plus size={18} />

                    Add Memory

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <div className={styles.search}>

                    <input
                        className={styles.searchInput}
                        placeholder="Search memory..."
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                    />

                </div>

                <select
                    className={styles.select}
                    value={type}
                    onChange={(e) =>
                        setType(
                            e.target.value as
                                | MemoryType
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>conversation</option>
                    <option>knowledge</option>
                    <option>document</option>
                    <option>code</option>
                    <option>preference</option>

                </select>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | MemoryStatus
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>active</option>
                    <option>archived</option>
                    <option>expired</option>

                </select>

            </section>

            {/* ================= STATS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Total Memory
                    </div>

                    <div className={styles.statValue}>
                        {statistics.total}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Active
                    </div>

                    <div className={styles.statValue}>
                        {statistics.active}
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

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Expired
                    </div>

                    <div className={styles.statValue}>
                        {statistics.expired}
                    </div>

                </div>

            </section>
                        {/* ================= MEMORY GRID ================= */}

            <section className={styles.grid}>

                {filteredMemory.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Memory Found
                        </h3>

                        <p className={styles.description}>
                            No memory entries match the current search or filters.
                        </p>

                    </div>

                ) : (

                    filteredMemory.map((memory) => (

                        <article
                            key={memory.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div>

                                <h3 className={styles.cardTitle}>
                                    {memory.title}
                                </h3>

                                <p className={styles.description}>
                                    {memory.description}
                                </p>

                            </div>

                            {/* ---------- Tags ---------- */}

                            <div className={styles.tags}>

                                {memory.tags.map((tag) => (

                                    <span
                                        key={tag}
                                        className={styles.tag}
                                    >
                                        #{tag}
                                    </span>

                                ))}

                            </div>

                            {/* ---------- Confidence ---------- */}

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

                                    <span>Confidence</span>

                                    <span>
                                        {memory.confidence}%
                                    </span>

                                </div>

                                <div className={styles.progress}>

                                    <div
                                        className={styles.progressFill}
                                        style={{
                                            width: `${memory.confidence}%`,
                                        }}
                                    />

                                </div>

                            </div>

                            {/* ---------- Importance ---------- */}

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

                                    <span>Importance</span>

                                    <span>
                                        {memory.importance}%
                                    </span>

                                </div>

                                <div className={styles.progress}>

                                    <div
                                        className={styles.progressFill}
                                        style={{
                                            width: `${memory.importance}%`,
                                        }}
                                    />

                                </div>

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Type
                                    </div>

                                    <div className={styles.metaValue}>
                                        {memory.type}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {memory.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Source
                                    </div>

                                    <div className={styles.metaValue}>
                                        {memory.source}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Updated
                                    </div>

                                    <div className={styles.metaValue}>
                                        {memory.updatedAt}
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    View
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Archive
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default Memory;