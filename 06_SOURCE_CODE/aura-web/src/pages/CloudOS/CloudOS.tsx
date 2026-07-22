import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import styles from "./CloudOS.module.css";

import type {
    CloudCluster,
    CloudProvider,
    ServiceStatus,
} from "./CloudOS.types";

const clusters: CloudCluster[] = [
    {
        id: "1",
        name: "Production Cluster",
        provider: "AWS",
        region: "ap-south-1",
        kubernetesVersion: "v1.31",
        nodes: 18,
        cpuUsage: 61,
        memoryUsage: 57,
        storageUsage: 49,
        status: "Healthy",
    },
    {
        id: "2",
        name: "AI Compute",
        provider: "Google Cloud",
        region: "asia-south1",
        kubernetesVersion: "v1.30",
        nodes: 12,
        cpuUsage: 78,
        memoryUsage: 69,
        storageUsage: 52,
        status: "Warning",
    },
    {
        id: "3",
        name: "Enterprise Backend",
        provider: "Azure",
        region: "Central India",
        kubernetesVersion: "v1.31",
        nodes: 10,
        cpuUsage: 42,
        memoryUsage: 46,
        storageUsage: 38,
        status: "Healthy",
    },
    {
        id: "4",
        name: "Disaster Recovery",
        provider: "Oracle Cloud",
        region: "Mumbai",
        kubernetesVersion: "v1.29",
        nodes: 8,
        cpuUsage: 21,
        memoryUsage: 25,
        storageUsage: 31,
        status: "Healthy",
    },
    {
        id: "5",
        name: "Private AI Cluster",
        provider: "Private Cloud",
        region: "On-Premise",
        kubernetesVersion: "v1.31",
        nodes: 20,
        cpuUsage: 91,
        memoryUsage: 88,
        storageUsage: 73,
        status: "Critical",
    },
];

const CloudOS = () => {

    const [provider, setProvider] =
        useState<CloudProvider | "All">("All");

    const [status, setStatus] =
        useState<ServiceStatus | "All">("All");

    const filteredClusters = useMemo(() => {

        return clusters.filter((cluster) => {

            const matchesProvider =
                provider === "All" ||
                cluster.provider === provider;

            const matchesStatus =
                status === "All" ||
                cluster.status === status;

            return (
                matchesProvider &&
                matchesStatus
            );

        });

    }, [provider, status]);

    const statistics = {

        clusters: clusters.length,

        nodes: clusters.reduce(
            (total, cluster) => total + cluster.nodes,
            0
        ),

        runningPods: 684,

        deployments: 124,

    };

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        CloudOS
                    </h1>

                    <p className={styles.subtitle}>
                        Unified cloud infrastructure and Kubernetes operations dashboard.
                    </p>

                </div>

                <button className={styles.primaryButton}>

                    <Plus size={18} />

                    New Cluster

                </button>

            </section>

            {/* ================= TOOLBAR ================= */}

            <section className={styles.toolbar}>

                <select
                    className={styles.select}
                    value={provider}
                    onChange={(e) =>
                        setProvider(
                            e.target.value as
                                | CloudProvider
                                | "All"
                        )
                    }
                >
                    <option>All</option>
                    <option>AWS</option>
                    <option>Azure</option>
                    <option>Google Cloud</option>
                    <option>Oracle Cloud</option>
                    <option>Private Cloud</option>
                </select>

                <select
                    className={styles.select}
                    value={status}
                    onChange={(e) =>
                        setStatus(
                            e.target.value as
                                | ServiceStatus
                                | "All"
                        )
                    }
                >
                    <option>All</option>
                    <option>Healthy</option>
                    <option>Warning</option>
                    <option>Critical</option>
                    <option>Offline</option>
                </select>

            </section>

            {/* ================= SUMMARY ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Clusters
                    </div>

                    <div className={styles.statValue}>
                        {statistics.clusters}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Nodes
                    </div>

                    <div className={styles.statValue}>
                        {statistics.nodes}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Running Pods
                    </div>

                    <div className={styles.statValue}>
                        {statistics.runningPods}
                    </div>

                </div>

                <div className={styles.statCard}>

                    <div className={styles.statTitle}>
                        Deployments
                    </div>

                    <div className={styles.statValue}>
                        {statistics.deployments}
                    </div>

                </div>

            </section>
                        {/* ================= CLUSTER GRID ================= */}

            <section className={styles.grid}>

                {filteredClusters.length === 0 ? (

                    <div className={styles.card}>

                        <h3 className={styles.cardTitle}>
                            No Clusters Found
                        </h3>

                        <p>
                            No Kubernetes clusters match the selected filters.
                        </p>

                    </div>

                ) : (

                    filteredClusters.map((cluster) => (

                        <article
                            key={cluster.id}
                            className={styles.card}
                        >

                            {/* ---------- Header ---------- */}

                            <div>

                                <h3 className={styles.cardTitle}>
                                    {cluster.name}
                                </h3>

                                <p>
                                    {cluster.provider} • {cluster.region}
                                </p>

                            </div>

                            {/* ---------- Metadata ---------- */}

                            <div className={styles.meta}>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Status
                                    </div>

                                    <div className={styles.metaValue}>
                                        {cluster.status}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Kubernetes
                                    </div>

                                    <div className={styles.metaValue}>
                                        {cluster.kubernetesVersion}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Nodes
                                    </div>

                                    <div className={styles.metaValue}>
                                        {cluster.nodes}
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        CPU Usage
                                    </div>

                                    <div className={styles.metaValue}>
                                        {cluster.cpuUsage}%
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Memory Usage
                                    </div>

                                    <div className={styles.metaValue}>
                                        {cluster.memoryUsage}%
                                    </div>

                                </div>

                                <div>

                                    <div className={styles.metaLabel}>
                                        Storage Usage
                                    </div>

                                    <div className={styles.metaValue}>
                                        {cluster.storageUsage}%
                                    </div>

                                </div>

                            </div>

                            {/* ---------- Footer ---------- */}

                            <div className={styles.footer}>

                                <button
                                    className={styles.footerButton}
                                >
                                    Deploy
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    Restart
                                </button>

                                <button
                                    className={styles.footerButton}
                                >
                                    View Logs
                                </button>

                            </div>

                        </article>

                    ))

                )}

            </section>

        </main>

    );

};

export default CloudOS;