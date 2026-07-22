import { useMemo, useState } from "react";
import { Download, Plus } from "lucide-react";

import styles from "./Models.module.css";

import type {
    AIModel,
    ModelProvider,
    ModelStatus,
} from "./Models.types";

const models: AIModel[] = [
    {
        id: "1",
        name: "GPT-5",
        provider: "OpenAI",
        deployment: "Cloud",
        status: "running",
        parameters: "Auto",
        contextWindow: 1000000,
        memoryUsage: "24 GB",
        tokenSpeed: "210 tok/s",
        latency: "210 ms",
        version: "v5",
    },
    {
        id: "2",
        name: "Claude Sonnet 4",
        provider: "Anthropic",
        deployment: "Cloud",
        status: "running",
        parameters: "Unknown",
        contextWindow: 200000,
        memoryUsage: "18 GB",
        tokenSpeed: "170 tok/s",
        latency: "260 ms",
        version: "4.0",
    },
    {
        id: "3",
        name: "Gemini 2.5 Pro",
        provider: "Google",
        deployment: "Cloud",
        status: "running",
        parameters: "Unknown",
        contextWindow: 1000000,
        memoryUsage: "20 GB",
        tokenSpeed: "205 tok/s",
        latency: "240 ms",
        version: "2.5",
    },
    {
        id: "4",
        name: "Llama 3.3 70B",
        provider: "Meta",
        deployment: "Local",
        status: "stopped",
        parameters: "70B",
        contextWindow: 131072,
        memoryUsage: "42 GB",
        tokenSpeed: "65 tok/s",
        latency: "650 ms",
        version: "3.3",
    },
    {
        id: "5",
        name: "Mistral Large",
        provider: "Mistral",
        deployment: "Cloud",
        status: "running",
        parameters: "123B",
        contextWindow: 128000,
        memoryUsage: "26 GB",
        tokenSpeed: "180 tok/s",
        latency: "290 ms",
        version: "Latest",
    },
    {
        id: "6",
        name: "DeepSeek R1 8B",
        provider: "Ollama",
        deployment: "Local",
        status: "downloading",
        parameters: "8B",
        contextWindow: 32768,
        memoryUsage: "8 GB",
        tokenSpeed: "48 tok/s",
        latency: "720 ms",
        version: "8B",
    },
];

const Models = () => {

    const [search, setSearch] = useState("");

    const [provider, setProvider] =
        useState<ModelProvider | "All">("All");

    const [status, setStatus] =
        useState<ModelStatus | "All">("All");

    const filteredModels = useMemo(() => {

        return models.filter((model) => {

            const matchesSearch =
                model.name
                    .toLowerCase()
                    .includes(search.toLowerCase());

            const matchesProvider =
                provider === "All" ||
                model.provider === provider;

            const matchesStatus =
                status === "All" ||
                model.status === status;

            return (
                matchesSearch &&
                matchesProvider &&
                matchesStatus
            );

        });

    }, [search, provider, status]);

    const statistics = {

        total: models.length,

        running: models.filter(
            (model) => model.status === "running"
        ).length,

        local: models.filter(
            (model) => model.deployment === "Local"
        ).length,

        cloud: models.filter(
            (model) => model.deployment === "Cloud"
        ).length,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        AI Models
                    </h1>

                    <p className={styles.subtitle}>
                        Deploy, monitor and manage enterprise AI models across
                        cloud and local infrastructure.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Plus size={18} />

                    Add Model

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <div className={styles.search}>

                    <input
                        className={styles.searchInput}
                        placeholder="Search models..."
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                    />

                </div>

                <select
                    className={styles.select}
                    value={provider}
                    onChange={(e) =>
                        setProvider(
                            e.target.value as
                                | ModelProvider
                                | "All"
                        )
                    }
                >
                    <option>All</option>
                    <option>OpenAI</option>
                    <option>Anthropic</option>
                    <option>Google</option>
                    <option>Meta</option>
                    <option>Mistral</option>
                    <option>Ollama</option>
                </select>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | ModelStatus
                                | "All"
                        )
                    }
                >
                    <option>All</option>
                    <option>running</option>
                    <option>stopped</option>
                    <option>downloading</option>
                    <option>error</option>
                </select>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>
                    <div className={styles.statTitle}>
                        Total Models
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
                        Local
                    </div>
                    <div className={styles.statValue}>
                        {statistics.local}
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statTitle}>
                        Cloud
                    </div>
                    <div className={styles.statValue}>
                        {statistics.cloud}
                    </div>
                </div>

            </section>
                        {/* ================= MODEL GRID ================= */}

            <section className={styles.grid}>

                {filteredModels.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Models Found
                        </h3>

                        <p className={styles.description}>
                            No AI models match the selected search criteria or
                            filters.
                        </p>

                    </div>

                ) : (

                    filteredModels.map((model) => (

                        <article
                            key={model.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div>

                                <h3 className={styles.cardTitle}>
                                    {model.name}
                                </h3>

                                <p className={styles.description}>
                                    {model.provider} • {model.deployment}
                                </p>

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Version
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.version}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Parameters
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.parameters}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Context Window
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.contextWindow.toLocaleString()}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Memory Usage
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.memoryUsage}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Token Speed
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.tokenSpeed}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Latency
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.latency}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Deployment
                                    </div>

                                    <div className={styles.metaValue}>
                                        {model.deployment}
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                {model.status === "downloading" ? (

                                    <button
                                        className={styles.footerButton}
                                    >
                                        Downloading...
                                    </button>

                                ) : model.status === "running" ? (

                                    <>
                                        <button
                                            className={styles.footerButton}
                                        >
                                            Stop
                                        </button>

                                        <button
                                            className={styles.footerButton}
                                        >
                                            Restart
                                        </button>
                                    </>

                                ) : (

                                    <>
                                        <button
                                            className={styles.footerButton}
                                        >
                                            Deploy
                                        </button>

                                        <button
                                            className={styles.footerButton}
                                        >
                                            <Download size={16} />

                                            Download
                                        </button>
                                    </>

                                )}

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default Models;