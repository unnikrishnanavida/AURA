import { useState } from "react";
import {
    Award,
    Building2,
    Calendar,
    Mail,
    MapPin,
    User,
} from "lucide-react";

import styles from "./Profile.module.css";

import type {
    Achievement,
    ProfileStatistics,
    UserProfile,
} from "./Profile.types";

const profile: UserProfile = {
    id: "USR-001",
    fullName: "John Carter",
    email: "john.carter@aura.ai",
    role: "Senior AI Engineer",
    organization: "AURA Technologies",
    department: "Artificial Intelligence",
    location: "New York, USA",
    bio:
        "Building enterprise-grade AI systems with a focus on scalable architectures, intelligent automation and secure cloud-native solutions.",
    joinedDate: "12 January 2024",
    avatar: "JC",
};

const statistics: ProfileStatistics = {
    projects: 28,
    workflows: 142,
    conversations: 1640,
    apiRequests: 842310,
};

const achievements: Achievement[] = [
    {
        id: "1",
        title: "AI Architect",
        description:
            "Designed and deployed 100+ enterprise AI workflows.",
        earnedOn: "March 2026",
    },
    {
        id: "2",
        title: "Top Contributor",
        description:
            "Recognized for outstanding engineering contributions.",
        earnedOn: "January 2026",
    },
    {
        id: "3",
        title: "Innovation Award",
        description:
            "Awarded for building next-generation AI solutions.",
        earnedOn: "October 2025",
    },
];

const Profile = () => {

    const [user] =
        useState<UserProfile>(profile);

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        My Profile
                    </h1>

                    <p className={styles.subtitle}>
                        Manage your personal information,
                        achievements and account details.
                    </p>

                </div>

                <button className={styles.editButton}>
                    Edit Profile
                </button>

            </header>

            {/* ================= GRID ================= */}

            <section className={styles.grid}>

                {/* ================= PROFILE CARD ================= */}

                <aside className={styles.card}>

                    <div className={styles.avatar}>
                        {user.avatar}
                    </div>

                    <h2 className={styles.name}>
                        {user.fullName}
                    </h2>

                    <div className={styles.role}>
                        {user.role}
                    </div>

                    <div className={styles.info}>

                        <div>

                            <div className={styles.label}>
                                <Mail size={15} />
                                {" "}Email
                            </div>

                            <div className={styles.value}>
                                {user.email}
                            </div>

                        </div>

                        <div>

                            <div className={styles.label}>
                                <Building2 size={15} />
                                {" "}Organization
                            </div>

                            <div className={styles.value}>
                                {user.organization}
                            </div>

                        </div>

                        <div>

                            <div className={styles.label}>
                                Department
                            </div>

                            <div className={styles.value}>
                                {user.department}
                            </div>

                        </div>

                        <div>

                            <div className={styles.label}>
                                <MapPin size={15} />
                                {" "}Location
                            </div>

                            <div className={styles.value}>
                                {user.location}
                            </div>

                        </div>

                        <div>

                            <div className={styles.label}>
                                <Calendar size={15} />
                                {" "}Joined
                            </div>

                            <div className={styles.value}>
                                {user.joinedDate}
                            </div>

                        </div>

                    </div>

                </aside>

                {/* ================= DETAILS ================= */}

                <section
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 24,
                    }}
                >

                    {/* ---------- BIO ---------- */}

                    <div className={styles.card}>

                        <h2>
                            <User size={20} />
                            {" "}About
                        </h2>

                        <p
                            style={{
                                color: "#CBD5E1",
                                lineHeight: 1.8,
                            }}
                        >
                            {user.bio}
                        </p>

                    </div>

                    {/* ---------- STATISTICS ---------- */}

                    <div className={styles.card}>

                        <h2>
                            Profile Statistics
                        </h2>

                        <div className={styles.stats}>

                            <div className={styles.statCard}>

                                <div
                                    className={styles.statValue}
                                >
                                    {statistics.projects}
                                </div>

                                <div
                                    className={styles.statLabel}
                                >
                                    Projects
                                </div>

                            </div>

                            <div className={styles.statCard}>

                                <div
                                    className={styles.statValue}
                                >
                                    {statistics.workflows}
                                </div>

                                <div
                                    className={styles.statLabel}
                                >
                                    Workflows
                                </div>

                            </div>

                            <div className={styles.statCard}>

                                <div
                                    className={styles.statValue}
                                >
                                    {statistics.conversations}
                                </div>

                                <div
                                    className={styles.statLabel}
                                >
                                    Conversations
                                </div>

                            </div>

                            <div className={styles.statCard}>

                                <div
                                    className={styles.statValue}
                                >
                                    {statistics.apiRequests.toLocaleString()}
                                </div>

                                <div
                                    className={styles.statLabel}
                                >
                                    API Requests
                                </div>

                            </div>

                        </div>

                    </div>

                    {/* ---------- ACHIEVEMENTS ---------- */}

                    <div className={styles.card}>

                        <h2>

                            <Award size={20} />

                            {" "}Achievements

                        </h2>

                        {achievements.map((achievement) => (

                            <div
                                key={achievement.id}
                                className={styles.timelineItem}
                            >

                                <div
                                    className={styles.itemTitle}
                                >
                                    {achievement.title}
                                </div>

                                <div
                                    className={styles.itemDescription}
                                >
                                    {achievement.description}
                                </div>

                                <div
                                    className={styles.itemTime}
                                >
                                    {achievement.earnedOn}
                                </div>

                            </div>

                        ))}

                    </div>
                                        {/* ---------- ACTIVITY TIMELINE ---------- */}

                    <div className={styles.card}>

                        <h2>Recent Activity</h2>

                        <div className={styles.timeline}>

                            <div className={styles.timelineItem}>

                                <div className={styles.itemTitle}>
                                    Workflow Published
                                </div>

                                <div className={styles.itemDescription}>
                                    Successfully deployed the Customer Support AI workflow.
                                </div>

                                <div className={styles.itemTime}>
                                    Today • 09:45 AM
                                </div>

                            </div>

                            <div className={styles.timelineItem}>

                                <div className={styles.itemTitle}>
                                    API Key Generated
                                </div>

                                <div className={styles.itemDescription}>
                                    Created a new production API key.
                                </div>

                                <div className={styles.itemTime}>
                                    Yesterday • 03:20 PM
                                </div>

                            </div>

                            <div className={styles.timelineItem}>

                                <div className={styles.itemTitle}>
                                    Security Scan Completed
                                </div>

                                <div className={styles.itemDescription}>
                                    No critical vulnerabilities were detected.
                                </div>

                                <div className={styles.itemTime}>
                                    2 Days Ago
                                </div>

                            </div>

                        </div>

                    </div>

                    {/* ---------- CONNECTED ACCOUNTS ---------- */}

                    <div className={styles.card}>

                        <h2>
                            Connected Accounts
                        </h2>

                        <div className={styles.connection}>

                            <div>

                                <div className={styles.itemTitle}>
                                    GitHub
                                </div>

                                <div className={styles.itemTime}>
                                    @johncarter
                                </div>

                            </div>

                            <span className={styles.status}>
                                Connected
                            </span>

                        </div>

                        <div className={styles.connection}>

                            <div>

                                <div className={styles.itemTitle}>
                                    Google
                                </div>

                                <div className={styles.itemTime}>
                                    john.carter@gmail.com
                                </div>

                            </div>

                            <span className={styles.status}>
                                Connected
                            </span>

                        </div>

                        <div className={styles.connection}>

                            <div>

                                <div className={styles.itemTitle}>
                                    Microsoft
                                </div>

                                <div className={styles.itemTime}>
                                    Azure Enterprise
                                </div>

                            </div>

                            <span className={styles.status}>
                                Connected
                            </span>

                        </div>

                    </div>

                    {/* ---------- ACCOUNT SUMMARY ---------- */}

                    <div className={styles.card}>

                        <h2>
                            Account Summary
                        </h2>

                        <div className={styles.info}>

                            <div>

                                <div className={styles.label}>
                                    Account Status
                                </div>

                                <div className={styles.value}>
                                    Active
                                </div>

                            </div>

                            <div>

                                <div className={styles.label}>
                                    Subscription
                                </div>

                                <div className={styles.value}>
                                    Enterprise
                                </div>

                            </div>

                            <div>

                                <div className={styles.label}>
                                    Storage Used
                                </div>

                                <div className={styles.value}>
                                    68 GB / 100 GB
                                </div>

                            </div>

                            <div>

                                <div className={styles.label}>
                                    Workspace
                                </div>

                                <div className={styles.value}>
                                    AURA Enterprise
                                </div>

                            </div>

                        </div>

                    </div>

                </section>

            </section>

        </main>

    );

};

export default Profile;