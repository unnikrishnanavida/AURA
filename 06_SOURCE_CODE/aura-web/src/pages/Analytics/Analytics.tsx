import { useState } from "react";
import { Download } from "lucide-react";
import { Line, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

import styles from "./Analytics.module.css";

import type {
    KPI,
    ResourceUsage,
    TimeRange,
    UsagePoint,
} from "./Analytics.types";

const kpis: KPI[] = [
    {
        id: "1",
        title: "AI Requests",
        value: "2.8M",
        change: 18.4,
        trend: "up",
    },
    {
        id: "2",
        title: "Generated Tokens",
        value: "847M",
        change: 14.7,
        trend: "up",
    },
    {
        id: "3",
        title: "Average Response",
        value: "248 ms",
        change: -6.2,
        trend: "down",
    },
    {
        id: "4",
        title: "Monthly Cost",
        value: "$14,280",
        change: 9.1,
        trend: "up",
    },
];

const usageData: UsagePoint[] = [
    {
        name: "Mon",
        requests: 12000,
        tokens: 5400000,
        cost: 320,
    },
    {
        name: "Tue",
        requests: 14800,
        tokens: 6200000,
        cost: 355,
    },
    {
        name: "Wed",
        requests: 17600,
        tokens: 7100000,
        cost: 398,
    },
    {
        name: "Thu",
        requests: 16400,
        tokens: 6800000,
        cost: 372,
    },
    {
        name: "Fri",
        requests: 19500,
        tokens: 8200000,
        cost: 445,
    },
    {
        name: "Sat",
        requests: 17100,
        tokens: 7340000,
        cost: 406,
    },
    {
        name: "Sun",
        requests: 15400,
        tokens: 6600000,
        cost: 368,
    },
];

const resources: ResourceUsage = {
    cpu: 46,
    gpu: 71,
    memory: 63,
    storage: 54,
};

const Analytics = () => {

    const [range, setRange] =
        useState<TimeRange>("7d");

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <section className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        Analytics Dashboard
                    </h1>

                    <p className={styles.subtitle}>
                        Enterprise AI performance, usage and infrastructure
                        monitoring.
                    </p>

                </div>

                <div className={styles.toolbar}>

                    <select
                        className={styles.select}
                        value={range}
                        onChange={(e) =>
                            setRange(
                                e.target.value as TimeRange
                            )
                        }
                    >

                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="90d">Last 90 Days</option>
                        <option value="1y">Last Year</option>

                    </select>

                    <button className={styles.button}>

                        <Download size={18} />

                        Export Report

                    </button>

                </div>

            </section>

            {/* ================= KPI CARDS ================= */}

            <section className={styles.kpiGrid}>

                {kpis.map((kpi) => (

                    <article
                        key={kpi.id}
                        className={styles.kpiCard}
                    >

                        <div className={styles.kpiTitle}>
                            {kpi.title}
                        </div>

                        <div className={styles.kpiValue}>
                            {kpi.value}
                        </div>

                        <div className={styles.kpiChange}>

                            {kpi.trend === "up"
                                ? "▲"
                                : "▼"}{" "}

                            {Math.abs(kpi.change)}%

                        </div>

                    </article>

                ))}

            </section>
                        {/* ================= DASHBOARD CONTENT ================= */}

            <section className={styles.content}>

                {/* ---------- Usage Chart ---------- */}

                <article className={styles.chartCard}>

                    <h2 className={styles.cardTitle}>
                        AI Request Trends
                    </h2>

                    <ResponsiveContainer
                        width="100%"
                        height={360}
                    >

                        <LineChart data={usageData}>

                            <CartesianGrid strokeDasharray="3 3" />

                            <XAxis dataKey="name" />

                            <YAxis />

                            <Tooltip />

                            <Legend />

                            <Line
                                type="monotone"
                                dataKey="requests"
                                name="Requests"
                                stroke="#D4AF37"
                                strokeWidth={3}
                            />

                            <Line
                                type="monotone"
                                dataKey="cost"
                                name="Cost"
                                stroke="#60A5FA"
                                strokeWidth={3}
                            />

                        </LineChart>

                    </ResponsiveContainer>

                </article>

                {/* ---------- Resource Usage ---------- */}

                <aside className={styles.resourceCard}>

                    <h2 className={styles.cardTitle}>
                        Infrastructure
                    </h2>

                    <div className={styles.resourceList}>

                        <div className={styles.resourceItem}>

                            <span>CPU Usage</span>

                            <strong>{resources.cpu}%</strong>

                        </div>

                        <div className={styles.resourceItem}>

                            <span>GPU Usage</span>

                            <strong>{resources.gpu}%</strong>

                        </div>

                        <div className={styles.resourceItem}>

                            <span>Memory</span>

                            <strong>{resources.memory}%</strong>

                        </div>

                        <div className={styles.resourceItem}>

                            <span>Storage</span>

                            <strong>{resources.storage}%</strong>

                        </div>

                    </div>

                </aside>

            </section>

        </main>

    );

};

export default Analytics;