import { useMemo, useState } from "react";
import {
    Activity,
    AlertTriangle,
    Eye,
    Shield,
    ShieldAlert,
    Users,
} from "lucide-react";

import styles from "./Security.module.css";

import type {
    ActiveSession,
    SecurityFilter,
    SecurityStatistics,
    SecurityThreat,
} from "./Security.types";

const statistics: SecurityStatistics = {
    activeThreats: 7,
    activeSessions: 143,
    blockedAttempts: 328,
    apiKeys: 19,
};

const threats: SecurityThreat[] = [
    {
        id: "TH-001",
        title: "Brute Force Login",
        source: "Authentication Service",
        severity: "High",
        status: "Warning",
        detectedAt: "5 mins ago",
        description:
            "Multiple failed login attempts detected from a single IP.",
    },
    {
        id: "TH-002",
        title: "Suspicious API Activity",
        source: "Gateway",
        severity: "Critical",
        status: "Critical",
        detectedAt: "12 mins ago",
        description:
            "API request volume exceeded normal baseline.",
    },
    {
        id: "TH-003",
        title: "Privilege Escalation",
        source: "IAM",
        severity: "Medium",
        status: "Healthy",
        detectedAt: "40 mins ago",
        description:
            "Administrative permission request requires review.",
    },
    {
        id: "TH-004",
        title: "Unknown Device Login",
        source: "Identity Center",
        severity: "Low",
        status: "Healthy",
        detectedAt: "1 hour ago",
        description:
            "User authenticated from a previously unseen device.",
    },
];

const sessions: ActiveSession[] = [
    {
        id: "S-101",
        user: "John Carter",
        ipAddress: "192.168.10.12",
        device: "MacBook Pro",
        location: "New York",
        lastActivity: "2 mins ago",
    },
    {
        id: "S-102",
        user: "Emma Watson",
        ipAddress: "192.168.10.20",
        device: "Windows 11",
        location: "London",
        lastActivity: "5 mins ago",
    },
    {
        id: "S-103",
        user: "David Kim",
        ipAddress: "192.168.10.34",
        device: "Ubuntu Desktop",
        location: "Seoul",
        lastActivity: "12 mins ago",
    },
];

const Security = () => {

    const [filter, setFilter] =
        useState<SecurityFilter>({
            severity: "All",
            status: "All",
        });

    const filteredThreats = useMemo(() => {

        return threats.filter((threat) => {

            const severityMatch =
                filter.severity === "All" ||
                threat.severity === filter.severity;

            const statusMatch =
                filter.status === "All" ||
                threat.status === filter.status;

            return severityMatch && statusMatch;

        });

    }, [filter]);

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        Security Center
                    </h1>

                    <p className={styles.subtitle}>
                        Monitor threats, sessions,
                        authentication and platform security.
                    </p>

                </div>

                <button className={styles.primaryButton}>
                    Security Scan
                </button>

            </header>

            {/* ================= FILTERS ================= */}

            <section className={styles.toolbar}>

                <select
                    className={styles.select}
                    value={filter.severity}
                    onChange={(e) =>
                        setFilter({
                            ...filter,
                            severity: e.target.value as SecurityFilter["severity"],
                        })
                    }
                >
                    <option>All</option>
                    <option>Low</option>
                    <option>Medium</option>
                    <option>High</option>
                    <option>Critical</option>
                </select>

                <select
                    className={styles.select}
                    value={filter.status}
                    onChange={(e) =>
                        setFilter({
                            ...filter,
                            status: e.target.value as SecurityFilter["status"],
                        })
                    }
                >
                    <option>All</option>
                    <option>Healthy</option>
                    <option>Warning</option>
                    <option>Critical</option>
                </select>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                <div className={styles.statCard}>
                    <ShieldAlert size={30} color="#D4AF37" />
                    <div className={styles.statTitle}>
                        Active Threats
                    </div>
                    <div className={styles.statValue}>
                        {statistics.activeThreats}
                    </div>
                </div>

                <div className={styles.statCard}>
                    <Users size={30} color="#D4AF37" />
                    <div className={styles.statTitle}>
                        Active Sessions
                    </div>
                    <div className={styles.statValue}>
                        {statistics.activeSessions}
                    </div>
                </div>

                <div className={styles.statCard}>
                    <Activity size={30} color="#D4AF37" />
                    <div className={styles.statTitle}>
                        Blocked Attempts
                    </div>
                    <div className={styles.statValue}>
                        {statistics.blockedAttempts}
                    </div>
                </div>

                <div className={styles.statCard}>
                    <Shield size={30} color="#D4AF37" />
                    <div className={styles.statTitle}>
                        API Keys
                    </div>
                    <div className={styles.statValue}>
                        {statistics.apiKeys}
                    </div>
                </div>

            </section>

            {/* ================= CONTENT ================= */}

            <section className={styles.grid}>
                            {/* ================= THREATS ================= */}

                {filteredThreats.map((threat) => (

                    <article
                        key={threat.id}
                        className={styles.card}
                    >

                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                            }}
                        >

                            <h2 className={styles.cardTitle}>
                                {threat.title}
                            </h2>

                            <AlertTriangle
                                size={24}
                                color={
                                    threat.severity === "Critical"
                                        ? "#EF4444"
                                        : threat.severity === "High"
                                        ? "#F97316"
                                        : threat.severity === "Medium"
                                        ? "#FACC15"
                                        : "#22C55E"
                                }
                            />

                        </div>

                        <p className={styles.description}>
                            {threat.description}
                        </p>

                        <div className={styles.meta}>

                            <div>

                                <div className={styles.metaLabel}>
                                    Source
                                </div>

                                <div className={styles.metaValue}>
                                    {threat.source}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    Severity
                                </div>

                                <div className={styles.metaValue}>
                                    {threat.severity}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    Status
                                </div>

                                <div className={styles.metaValue}>
                                    {threat.status}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    Detected
                                </div>

                                <div className={styles.metaValue}>
                                    {threat.detectedAt}
                                </div>

                            </div>

                        </div>

                        <div className={styles.footer}>

                            <button className={styles.footerButton}>
                                <Eye size={16} />
                                {" "}View Details
                            </button>

                            <button className={styles.footerButton}>
                                Investigate
                            </button>

                        </div>

                    </article>

                ))}

                {/* ================= ACTIVE SESSIONS ================= */}

                {sessions.map((session) => (

                    <article
                        key={session.id}
                        className={styles.card}
                    >

                        <h2 className={styles.cardTitle}>
                            Active Session
                        </h2>

                        <div className={styles.meta}>

                            <div>

                                <div className={styles.metaLabel}>
                                    User
                                </div>

                                <div className={styles.metaValue}>
                                    {session.user}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    Device
                                </div>

                                <div className={styles.metaValue}>
                                    {session.device}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    IP Address
                                </div>

                                <div className={styles.metaValue}>
                                    {session.ipAddress}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    Location
                                </div>

                                <div className={styles.metaValue}>
                                    {session.location}
                                </div>

                            </div>

                            <div>

                                <div className={styles.metaLabel}>
                                    Last Activity
                                </div>

                                <div className={styles.metaValue}>
                                    {session.lastActivity}
                                </div>

                            </div>

                        </div>

                        <div className={styles.footer}>

                            <button className={styles.footerButton}>
                                Monitor
                            </button>

                            <button className={styles.footerButton}>
                                Block IP
                            </button>

                        </div>

                    </article>

                ))}
            </section>
        </main>

    );

};

export default Security;