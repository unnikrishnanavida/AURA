import {
    Activity,
    Cpu,
    Database,
    Server,
    Shield,
    Users,
} from "lucide-react";

import styles from "./Admin.module.css";

import type {
    AdminProps,
    AdminUser,
    AuditLog,
    InfrastructureService,
    SystemMetric,
} from "./Admin.types";

const metrics: SystemMetric[] = [
    {
        label: "Organizations",
        value: "124",
        change: "+12%",
    },
    {
        label: "Active Users",
        value: "18,492",
        change: "+6.8%",
    },
    {
        label: "API Requests",
        value: "42.8M",
        change: "+14%",
    },
    {
        label: "System Uptime",
        value: "99.99%",
        change: "+0.02%",
    },
];

const users: AdminUser[] = [
    {
        id: "1",
        name: "Sophia Carter",
        email: "sophia@aura.ai",
        role: "Super Admin",
        status: "Active",
    },
    {
        id: "2",
        name: "James Wilson",
        email: "james@aura.ai",
        role: "Organization Admin",
        status: "Active",
    },
    {
        id: "3",
        name: "Emma Johnson",
        email: "emma@aura.ai",
        role: "Developer",
        status: "Pending",
    },
    {
        id: "4",
        name: "Noah Smith",
        email: "noah@aura.ai",
        role: "Analyst",
        status: "Inactive",
    },
];

const services: InfrastructureService[] = [
    {
        id: "1",
        name: "Authentication Service",
        status: "Healthy",
        uptime: "99.99%",
    },
    {
        id: "2",
        name: "Vector Database",
        status: "Healthy",
        uptime: "99.95%",
    },
    {
        id: "3",
        name: "LLM Gateway",
        status: "Warning",
        uptime: "98.84%",
    },
    {
        id: "4",
        name: "Analytics Engine",
        status: "Healthy",
        uptime: "99.92%",
    },
];

const auditLogs: AuditLog[] = [
    {
        id: "1",
        user: "Sophia Carter",
        action: "Updated RBAC policies",
        timestamp: "2 minutes ago",
    },
    {
        id: "2",
        user: "James Wilson",
        action: "Created Organization",
        timestamp: "18 minutes ago",
    },
    {
        id: "3",
        user: "Emma Johnson",
        action: "Generated API Key",
        timestamp: "42 minutes ago",
    },
];

const Admin = ({
    className,
}: AdminProps) => {

    return (

        <main
            className={`${styles.page} ${className ?? ""}`}
        >

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        Administration Center
                    </h1>

                    <p className={styles.subtitle}>
                        Manage organizations, infrastructure,
                        users, permissions and enterprise
                        platform operations.
                    </p>

                </div>

                <button className={styles.actionButton}>
                    Open Control Center
                </button>

            </header>

            {/* ================= METRICS ================= */}

            <section className={styles.metrics}>

                {metrics.map((metric) => (

                    <article
                        key={metric.label}
                        className={styles.metricCard}
                    >

                        <div className={styles.metricValue}>
                            {metric.value}
                        </div>

                        <div className={styles.metricLabel}>
                            {metric.label}
                        </div>

                        <div className={styles.metricChange}>
                            {metric.change}
                        </div>

                    </article>

                ))}

            </section>

            {/* ================= MAIN LAYOUT ================= */}

            <section className={styles.layout}>

                {/* ================= USER MANAGEMENT ================= */}

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <Users size={20} />

                        {" "}

                        Organization Users

                    </h2>

                    <div className={styles.userList}>

                        {users.map((user) => (

                            <article
                                key={user.id}
                                className={styles.userCard}
                            >

                                <div className={styles.userName}>
                                    {user.name}
                                </div>

                                <div className={styles.userEmail}>
                                    {user.email}
                                </div>

                                <div className={styles.role}>
                                    {user.role}
                                </div>

                                <span className={styles.status}>
                                    {user.status}
                                </span>

                            </article>

                        ))}

                    </div>

                </section>

                {/* ================= INFRASTRUCTURE ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <Server size={20} />

                        {" "}

                        Infrastructure

                    </h2>

                    <div className={styles.serviceList}>

                        {services.map((service) => (

                            <article
                                key={service.id}
                                className={styles.serviceCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent:
                                            "space-between",
                                        alignItems: "center",
                                    }}
                                >

                                    <Database
                                        size={20}
                                        color="#D4AF37"
                                    />

                                    <span
                                        className={styles.status}
                                    >
                                        {service.status}
                                    </span>

                                </div>

                                <div
                                    style={{
                                        marginTop: 14,
                                        fontWeight: 600,
                                        color: "#FFF",
                                    }}
                                >
                                    {service.name}
                                </div>

                                <div
                                    style={{
                                        marginTop: 8,
                                        color: "#94A3B8",
                                    }}
                                >
                                    Uptime: {service.uptime}
                                </div>

                            </article>

                        ))}

                    </div>

                </aside>

            </section>
                        {/* ================= ADMIN OPERATIONS ================= */}

            <section className={styles.layout}>

                {/* ================= AUDIT LOGS ================= */}

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <Activity size={20} />

                        {" "}

                        Audit Logs

                    </h2>

                    <div className={styles.auditList}>

                        {auditLogs.map((log) => (

                            <article
                                key={log.id}
                                className={styles.auditCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                    }}
                                >

                                    <strong>
                                        {log.user}
                                    </strong>

                                    <span
                                        style={{
                                            color: "#94A3B8",
                                            fontSize: ".9rem",
                                        }}
                                    >
                                        {log.timestamp}
                                    </span>

                                </div>

                                <div
                                    style={{
                                        marginTop: 10,
                                        color: "#D4AF37",
                                    }}
                                >
                                    {log.action}
                                </div>

                            </article>

                        ))}

                    </div>

                </section>

                {/* ================= SECURITY ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <Shield size={20} />

                        {" "}

                        Security Overview

                    </h2>

                    <div className={styles.serviceList}>

                        {[
                            {
                                title: "RBAC Policies",
                                value: "248",
                            },
                            {
                                title: "API Keys",
                                value: "1,482",
                            },
                            {
                                title: "SSO Providers",
                                value: "12",
                            },
                            {
                                title: "MFA Adoption",
                                value: "97%",
                            },
                            {
                                title: "Security Alerts",
                                value: "2",
                            },
                        ].map((item) => (

                            <article
                                key={item.title}
                                className={styles.serviceCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                    }}
                                >

                                    <span>
                                        {item.title}
                                    </span>

                                    <strong
                                        style={{
                                            color: "#D4AF37",
                                        }}
                                    >
                                        {item.value}
                                    </strong>

                                </div>

                            </article>

                        ))}

                    </div>

                </aside>

            </section>

            {/* ================= CLUSTER HEALTH ================= */}

            <section className={styles.panel}>

                <h2 className={styles.panelTitle}>

                    <Cpu size={20} />

                    {" "}

                    Cluster Health

                </h2>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit,minmax(220px,1fr))",
                        gap: 18,
                    }}
                >

                    {[
                        {
                            title: "Inference Cluster",
                            status: "Healthy",
                        },
                        {
                            title: "Database Cluster",
                            status: "Healthy",
                        },
                        {
                            title: "GPU Pool",
                            status: "High Load",
                        },
                        {
                            title: "Redis Cache",
                            status: "Healthy",
                        },
                        {
                            title: "Kubernetes",
                            status: "Healthy",
                        },
                        {
                            title: "Vector Store",
                            status: "Healthy",
                        },
                    ].map((cluster) => (

                        <article
                            key={cluster.title}
                            className={styles.serviceCard}
                        >

                            <div
                                style={{
                                    fontWeight: 600,
                                    color: "#FFF",
                                }}
                            >
                                {cluster.title}
                            </div>

                            <span className={styles.status}>
                                {cluster.status}
                            </span>

                        </article>

                    ))}

                </div>

            </section>

            {/* ================= QUICK ACTIONS ================= */}

            <section className={styles.panel}>

                <h2 className={styles.panelTitle}>
                    Administration Actions
                </h2>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit,minmax(220px,1fr))",
                        gap: 20,
                    }}
                >

                    {[
                        "Create Organization",
                        "Invite User",
                        "Manage Roles",
                        "Generate API Key",
                        "Feature Flags",
                        "System Settings",
                        "Export Audit Logs",
                        "Backup Database",
                        "Restart Services",
                        "View Billing",
                        "Monitor AI Models",
                        "Open Admin Console",
                    ].map((action) => (

                        <button
                            key={action}
                            className={styles.actionButton}
                        >
                            {action}
                        </button>

                    ))}

                </div>

            </section>

        </main>

    );

};

export default Admin;