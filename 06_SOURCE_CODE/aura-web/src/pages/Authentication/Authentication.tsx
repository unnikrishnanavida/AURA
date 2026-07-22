import { useNavigate } from "react-router-dom";
import {
    ArrowRight,
    Bot,
    BrainCircuit,
    ShieldCheck,
    Sparkles,
} from "lucide-react";

import styles from "./Authentication.module.css";

import type {
    AuthenticationProps,
    AuthProvider,
} from "./Authentication.types";

const providers: AuthProvider[] = [
    {
        id: "google",
        name: "Continue with Google",
        icon: "G",
    },
    {
        id: "github",
        name: "Continue with GitHub",
        icon: "GH",
    },
    {
        id: "microsoft",
        name: "Continue with Microsoft",
        icon: "MS",
    },
    {
        id: "apple",
        name: "Continue with Apple",
        icon: "",
    },
];

const Authentication = ({
    className,
}: AuthenticationProps) => {

    const navigate = useNavigate();

    return (

        <main
            className={`${styles.page} ${className ?? ""}`}
        >

            <section className={styles.container}>

                {/* ================= HERO ================= */}

                <section className={styles.hero}>

                    <div className={styles.logo}>
                        AURA
                    </div>

                    <h1 className={styles.heading}>

                        Secure Enterprise

                        <br />

                        <span className={styles.highlight}>
                            Authentication
                        </span>

                    </h1>

                    <p className={styles.description}>

                        Access your intelligent workspace
                        securely with enterprise-grade
                        authentication, multi-provider sign in,
                        and AI-powered identity management.

                    </p>

                    <div className={styles.featureList}>

                        <div className={styles.feature}>

                            <ShieldCheck size={22} />

                            <span>
                                Enterprise Security
                            </span>

                        </div>

                        <div className={styles.feature}>

                            <BrainCircuit size={22} />

                            <span>
                                AI Identity Verification
                            </span>

                        </div>

                        <div className={styles.feature}>

                            <Bot size={22} />

                            <span>
                                Intelligent Workspace Access
                            </span>

                        </div>

                        <div className={styles.feature}>

                            <Sparkles size={22} />

                            <span>
                                Single Sign-On Ready
                            </span>

                        </div>

                    </div>

                </section>

                {/* ================= AUTH CARD ================= */}

                <section className={styles.card}>

                    <div>

                        <h2 className={styles.title}>
                            Welcome to AURA
                        </h2>

                        <p className={styles.subtitle}>
                            Continue by signing in or creating
                            a new enterprise workspace.
                        </p>

                    </div>

                    {/* ---------- SIGN IN ---------- */}

                    <button
                        className={`${styles.actionButton} ${styles.primary}`}
                        onClick={() =>
                            navigate("/login")
                        }
                    >

                        Sign In

                        {" "}

                        <ArrowRight size={18} />

                    </button>

                    {/* ---------- CREATE ACCOUNT ---------- */}

                    <button
                        className={`${styles.actionButton} ${styles.secondary}`}
                        onClick={() =>
                            navigate("/register")
                        }
                    >

                        Create Account

                    </button>

                    {/* ---------- DIVIDER ---------- */}

                    <div className={styles.divider}>
                        OR CONTINUE WITH
                    </div>
                                        {/* ---------- SOCIAL PROVIDERS ---------- */}

                    <div className={styles.socialGrid}>

                        {providers.map((provider) => (

                            <button
                                key={provider.id}
                                type="button"
                                className={styles.socialButton}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "space-between",
                                    }}
                                >

                                    <div
                                        style={{
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 16,
                                        }}
                                    >

                                        <div
                                            style={{
                                                width: 42,
                                                height: 42,
                                                borderRadius: 12,
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                background:
                                                    "rgba(212,175,55,.12)",
                                                fontWeight: 700,
                                            }}
                                        >
                                            {provider.icon}
                                        </div>

                                        <span>
                                            {provider.name}
                                        </span>

                                    </div>

                                    <ArrowRight size={18} />

                                </div>

                            </button>

                        ))}

                    </div>

                    {/* ---------- ENTERPRISE NOTICE ---------- */}

                    <div
                        style={{
                            padding: 18,
                            borderRadius: 14,
                            background:
                                "rgba(212,175,55,.08)",
                            border:
                                "1px solid rgba(212,175,55,.15)",
                        }}
                    >

                        <strong
                            style={{
                                color: "#D4AF37",
                            }}
                        >
                            Enterprise Ready
                        </strong>

                        <p
                            style={{
                                marginTop: 8,
                                color: "#CBD5E1",
                                lineHeight: 1.7,
                            }}
                        >
                            Supports Single Sign-On (SSO),
                            OAuth 2.0, OpenID Connect,
                            Multi-Factor Authentication,
                            and enterprise identity
                            providers including Azure AD,
                            Okta, Auth0 and Google
                            Workspace.
                        </p>

                    </div>

                    {/* ---------- FOOTER ---------- */}

                    <div className={styles.footer}>

                        By continuing you agree to the{" "}

                        <a href="/terms">
                            Terms
                        </a>

                        {" "}and{" "}

                        <a href="/privacy">
                            Privacy Policy
                        </a>

                    </div>

                </section>

            </section>

        </main>

    );

};

export default Authentication;