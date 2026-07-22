import { useMemo, useState } from "react";
import { Upload } from "lucide-react";

import styles from "./Files.module.css";

import type {
    FileItem,
    FileStatus,
    FileType,
} from "./Files.types";

const filesData: FileItem[] = [
    {
        id: "1",
        name: "Enterprise_Architecture.pdf",
        type: "document",
        status: "synced",
        size: "12.5 MB",
        owner: "Architecture Team",
        modifiedAt: "2026-07-20",
        favorite: true,
        shared: true,
        aiIndexed: true,
    },
    {
        id: "2",
        name: "Dashboard_UI.fig",
        type: "image",
        status: "synced",
        size: "4.8 MB",
        owner: "Design Team",
        modifiedAt: "2026-07-19",
        favorite: false,
        shared: true,
        aiIndexed: true,
    },
    {
        id: "3",
        name: "Backend_Source.zip",
        type: "archive",
        status: "processing",
        size: "145 MB",
        owner: "Development Team",
        modifiedAt: "2026-07-18",
        favorite: false,
        shared: false,
        aiIndexed: false,
    },
    {
        id: "4",
        name: "Knowledge_Base",
        type: "folder",
        status: "synced",
        size: "--",
        owner: "AURA",
        modifiedAt: "2026-07-20",
        favorite: true,
        shared: true,
        aiIndexed: true,
    },
];

const Files = () => {

    const [search, setSearch] = useState("");

    const [type, setType] =
        useState<FileType | "All">("All");

    const [status, setStatus] =
        useState<FileStatus | "All">("All");

    const filteredFiles = useMemo(() => {

        return filesData.filter((file) => {

            const matchesSearch =
                file.name
                    .toLowerCase()
                    .includes(search.toLowerCase());

            const matchesType =
                type === "All" ||
                file.type === type;

            const matchesStatus =
                status === "All" ||
                file.status === status;

            return (
                matchesSearch &&
                matchesType &&
                matchesStatus
            );

        });

    }, [search, type, status]);

    const statistics = {

        totalFiles: filesData.length,

        totalStorage: "1 TB",

        usedStorage: "384 GB",

        aiIndexed: filesData.filter(
            (file) => file.aiIndexed
        ).length,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        Enterprise Files
                    </h1>

                    <p className={styles.subtitle}>
                        Secure document management,
                        AI indexing and enterprise storage.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Upload size={18} />

                    Upload Files

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <div className={styles.search}>

                    <input
                        className={styles.searchInput}
                        placeholder="Search files..."
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
                                | FileType
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>folder</option>
                    <option>document</option>
                    <option>image</option>
                    <option>video</option>
                    <option>audio</option>
                    <option>code</option>
                    <option>archive</option>

                </select>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | FileStatus
                                | "All"
                        )
                    }
                >

                    <option>All</option>
                    <option>synced</option>
                    <option>uploading</option>
                    <option>processing</option>
                    <option>failed</option>

                </select>

            </section>

            {/* ================= STORAGE STATS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Total Files
                    </div>

                    <div className={styles.statValue}>
                        {statistics.totalFiles}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Total Storage
                    </div>

                    <div className={styles.statValue}>
                        {statistics.totalStorage}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Used Storage
                    </div>

                    <div className={styles.statValue}>
                        {statistics.usedStorage}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        AI Indexed
                    </div>

                    <div className={styles.statValue}>
                        {statistics.aiIndexed}
                    </div>

                </div>

            </section>
                        {/* ================= FILE GRID ================= */}

            <section className={styles.grid}>

                {filteredFiles.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.fileName}>
                            No Files Found
                        </h3>

                        <p className={styles.subtitle}>
                            No files match the current search or filters.
                        </p>

                    </div>

                ) : (

                    filteredFiles.map((file) => (

                        <article
                            key={file.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div className={styles.cardHeader}>

                                <div>

                                    <h3 className={styles.fileName}>
                                        {file.name}
                                    </h3>

                                    <span className={styles.fileType}>
                                        {file.type.toUpperCase()}
                                    </span>

                                </div>

                            </div>

                            {/* ---------- Badges ---------- */}

                            <div className={styles.badges}>

                                {file.favorite && (
                                    <span className={styles.badge}>
                                        ⭐ Favorite
                                    </span>
                                )}

                                {file.shared && (
                                    <span className={styles.badge}>
                                        👥 Shared
                                    </span>
                                )}

                                {file.aiIndexed && (
                                    <span className={styles.badge}>
                                        🤖 AI Indexed
                                    </span>
                                )}

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Size
                                    </div>

                                    <div className={styles.metaValue}>
                                        {file.size}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {file.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Owner
                                    </div>

                                    <div className={styles.metaValue}>
                                        {file.owner}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Modified
                                    </div>

                                    <div className={styles.metaValue}>
                                        {file.modifiedAt}
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    Download
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Rename
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Delete
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default Files;