import { useState } from "react";
import {
    Bell,
    Brain,
    Globe,
    Moon,
    Shield,
    User,
} from "lucide-react";

import styles from "./Settings.module.css";

import type {
    ApiKey,
    UserSettings,
} from "./Settings.types";

const apiKeys: ApiKey[] = [
    {
        id: "1",
        name: "Production API",
        createdAt: "12 Jun 2026",
        lastUsed: "2 mins ago",
        status: "Active",
    },
    {
        id: "2",
        name: "Development API",
        createdAt: "20 May 2026",
        lastUsed: "Yesterday",
        status: "Active",
    },
    {
        id: "3",
        name: "Legacy API",
        createdAt: "04 Mar 2026",
        lastUsed: "3 months ago",
        status: "Revoked",
    },
];

const Settings = () => {

    const [settings, setSettings] =
        useState<UserSettings>({
            fullName: "John Carter",
            email: "john.carter@aura.ai",
            organization: "AURA Technologies",
            defaultModel: "GPT-5",
            theme: "Dark",
            language: "English",
            timezone: "UTC +05:30",
            notifications: "Important",
            autoSave: true,
            analytics: true,
            twoFactorAuth: true,
        });

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        Settings
                    </h1>

                    <p className={styles.subtitle}>
                        Manage your account, AI preferences,
                        security and application settings.
                    </p>

                </div>

                <button className={styles.saveButton}>
                    Save Changes
                </button>

            </header>

            {/* ================= SETTINGS GRID ================= */}

            <section className={styles.grid}>

                {/* ================= PROFILE ================= */}

                <div className={styles.card}>

                    <h2 className={styles.cardTitle}>
                        <User size={20} />
                        {" "}Profile
                    </h2>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Full Name
                        </label>

                        <input
                            className={styles.input}
                            value={settings.fullName}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    fullName:e.target.value,
                                })
                            }
                        />

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Email Address
                        </label>

                        <input
                            className={styles.input}
                            value={settings.email}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    email:e.target.value,
                                })
                            }
                        />

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Organization
                        </label>

                        <input
                            className={styles.input}
                            value={settings.organization}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    organization:e.target.value,
                                })
                            }
                        />

                    </div>

                </div>

                {/* ================= AI ================= */}

                <div className={styles.card}>

                    <h2 className={styles.cardTitle}>
                        <Brain size={20} />
                        {" "}AI Preferences
                    </h2>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Default Model
                        </label>

                        <select
                            className={styles.select}
                            value={settings.defaultModel}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    defaultModel:e.target.value,
                                })
                            }
                        >

                            <option>GPT-5</option>
                            <option>Claude Sonnet 4</option>
                            <option>Gemini 2.5 Pro</option>
                            <option>Llama 3.3 70B</option>
                            <option>DeepSeek R1</option>

                        </select>

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Theme
                        </label>

                        <select
                            className={styles.select}
                            value={settings.theme}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    theme:e.target.value as UserSettings["theme"],
                                })
                            }
                        >

                            <option>Dark</option>
                            <option>Light</option>
                            <option>System</option>

                        </select>

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Language
                        </label>

                        <input
                            className={styles.input}
                            value={settings.language}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    language:e.target.value,
                                })
                            }
                        />

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Timezone
                        </label>

                        <input
                            className={styles.input}
                            value={settings.timezone}
                            onChange={(e)=>
                                setSettings({
                                    ...settings,
                                    timezone:e.target.value,
                                })
                            }
                        />

                    </div>

                </div>
                                {/* ================= NOTIFICATIONS ================= */}

                <div className={styles.card}>

                    <h2 className={styles.cardTitle}>
                        <Bell size={20} />
                        {" "}Notifications
                    </h2>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Notification Level
                        </label>

                        <select
                            className={styles.select}
                            value={settings.notifications}
                            onChange={(e) =>
                                setSettings({
                                    ...settings,
                                    notifications:
                                        e.target
                                            .value as UserSettings["notifications"],
                                })
                            }
                        >

                            <option>All</option>
                            <option>Important</option>
                            <option>Critical</option>
                            <option>None</option>

                        </select>

                    </div>

                    <div className={styles.checkboxRow}>

                        <span className={styles.checkboxLabel}>
                            Enable Auto Save
                        </span>

                        <input
                            type="checkbox"
                            className={styles.checkbox}
                            checked={settings.autoSave}
                            onChange={(e) =>
                                setSettings({
                                    ...settings,
                                    autoSave: e.target.checked,
                                })
                            }
                        />

                    </div>

                </div>

                {/* ================= SECURITY ================= */}

                <div className={styles.card}>

                    <h2 className={styles.cardTitle}>
                        <Shield size={20} />
                        {" "}Security
                    </h2>

                    <div className={styles.checkboxRow}>

                        <span className={styles.checkboxLabel}>
                            Two Factor Authentication
                        </span>

                        <input
                            type="checkbox"
                            className={styles.checkbox}
                            checked={settings.twoFactorAuth}
                            onChange={(e) =>
                                setSettings({
                                    ...settings,
                                    twoFactorAuth:
                                        e.target.checked,
                                })
                            }
                        />

                    </div>

                    <div className={styles.checkboxRow}>

                        <span className={styles.checkboxLabel}>
                            Usage Analytics
                        </span>

                        <input
                            type="checkbox"
                            className={styles.checkbox}
                            checked={settings.analytics}
                            onChange={(e) =>
                                setSettings({
                                    ...settings,
                                    analytics:
                                        e.target.checked,
                                })
                            }
                        />

                    </div>

                    <div
                        style={{
                            marginTop: 20,
                            display: "flex",
                            flexDirection: "column",
                            gap: 14,
                        }}
                    >

                        <button
                            className={styles.saveButton}
                        >
                            Enable Security Scan
                        </button>

                        <button
                            className={styles.saveButton}
                        >
                            Reset Settings
                        </button>

                    </div>

                </div>

                {/* ================= API KEYS ================= */}

                <div
                    className={styles.card}
                    style={{ gridColumn: "1 / -1" }}
                >

                    <h2 className={styles.cardTitle}>
                        <Globe size={20} />
                        {" "}API Keys
                    </h2>

                    {apiKeys.map((key) => (

                        <div
                            key={key.id}
                            className={styles.apiCard}
                        >

                            <div className={styles.apiInfo}>

                                <div
                                    className={styles.apiTitle}
                                >
                                    {key.name}
                                </div>

                                <div
                                    className={styles.apiMeta}
                                >
                                    Created: {key.createdAt}
                                </div>

                                <div
                                    className={styles.apiMeta}
                                >
                                    Last Used: {key.lastUsed}
                                </div>

                            </div>

                            <span
                                className={styles.status}
                            >
                                {key.status}
                            </span>

                        </div>

                    ))}

                </div>

                {/* ================= SUMMARY ================= */}

                <div
                    className={styles.card}
                    style={{ gridColumn: "1 / -1" }}
                >

                    <h2 className={styles.cardTitle}>
                        <Moon size={20} />
                        {" "}Configuration Summary
                    </h2>

                    <p className={styles.label}>
                        Theme:
                        <strong> {settings.theme}</strong>
                    </p>

                    <p className={styles.label}>
                        Model:
                        <strong> {settings.defaultModel}</strong>
                    </p>

                    <p className={styles.label}>
                        Language:
                        <strong> {settings.language}</strong>
                    </p>

                    <p className={styles.label}>
                        Notifications:
                        <strong> {settings.notifications}</strong>
                    </p>

                </div>

            </section>

        </main>

    );

};

export default Settings;