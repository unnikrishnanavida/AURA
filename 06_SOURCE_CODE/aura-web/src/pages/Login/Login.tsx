import { useState } from "react";
import {
    CheckCircle2,
    Eye,
    EyeOff,
    Lock,
    Mail,
    ShieldCheck,
    Sparkles,
} from "lucide-react";

import styles from "./Login.module.css";

import type {
    LoginForm,
    SocialProvider,
} from "./Login.types";

const socialProviders: SocialProvider[] = [
    {
        id: "google",
        name: "Google",
        icon: "G",
    },
    {
        id: "github",
        name: "GitHub",
        icon: "GH",
    },
    {
        id: "microsoft",
        name: "Microsoft",
        icon: "MS",
    },
];

const Login = () => {

    const [showPassword, setShowPassword] =
        useState(false);

    const [form, setForm] =
        useState<LoginForm>({
            email: "",
            password: "",
            rememberMe: true,
        });

    return (

        <main className={styles.page}>

            <section className={styles.container}>

                {/* ================= HERO ================= */}

                <section className={styles.hero}>

                    <div className={styles.logo}>
                        AURA
                    </div>

                    <h1 className={styles.heading}>
                        Enterprise AI Platform
                    </h1>

                    <p className={styles.description}>
                        Build, deploy and manage intelligent
                        AI systems from one unified platform.
                        Secure, scalable and production ready.
                    </p>

                    <div className={styles.featureList}>

                        <div className={styles.feature}>
                            <ShieldCheck size={20} />
                            Enterprise-grade security
                        </div>

                        <div className={styles.feature}>
                            <Sparkles size={20} />
                            AI Workflow Automation
                        </div>

                        <div className={styles.feature}>
                            <CheckCircle2 size={20} />
                            Multi-model AI Support
                        </div>

                    </div>

                </section>

                {/* ================= LOGIN CARD ================= */}

                <section className={styles.card}>

                    <div>

                        <h2 className={styles.title}>
                            Welcome Back
                        </h2>

                        <p className={styles.subtitle}>
                            Sign in to continue to AURA.
                        </p>

                    </div>

                    {/* ---------- EMAIL ---------- */}

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Email Address
                        </label>

                        <div className={styles.inputWrapper}>

                            <input
                                type="email"
                                className={styles.input}
                                placeholder="name@company.com"
                                value={form.email}
                                onChange={(e) =>
                                    setForm({
                                        ...form,
                                        email: e.target.value,
                                    })
                                }
                            />

                            <button
                                type="button"
                                className={styles.iconButton}
                            >
                                <Mail size={18} />
                            </button>

                        </div>

                    </div>

                    {/* ---------- PASSWORD ---------- */}

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Password
                        </label>

                        <div className={styles.inputWrapper}>

                            <input
                                type={
                                    showPassword
                                        ? "text"
                                        : "password"
                                }
                                className={styles.input}
                                placeholder="Enter password"
                                value={form.password}
                                onChange={(e) =>
                                    setForm({
                                        ...form,
                                        password: e.target.value,
                                    })
                                }
                            />

                            <button
                                type="button"
                                className={styles.iconButton}
                                onClick={() =>
                                    setShowPassword(
                                        !showPassword
                                    )
                                }
                            >

                                {showPassword ? (
                                    <EyeOff size={18} />
                                ) : (
                                    <Eye size={18} />
                                )}

                            </button>

                        </div>

                    </div>

                    {/* ---------- OPTIONS ---------- */}

                    <div className={styles.row}>

                        <label className={styles.checkbox}>

                            <input
                                type="checkbox"
                                checked={form.rememberMe}
                                onChange={(e) =>
                                    setForm({
                                        ...form,
                                        rememberMe:
                                            e.target.checked,
                                    })
                                }
                            />

                            Remember Me

                        </label>

                        <a
                            href="/forgot-password"
                            className={styles.link}
                        >
                            Forgot Password?
                        </a>

                    </div>
                                        {/* ---------- LOGIN BUTTON ---------- */}

                    <button
                        className={styles.loginButton}
                        type="button"
                    >
                        <Lock size={18} />

                        {" "}Sign In

                    </button>

                    {/* ---------- DIVIDER ---------- */}

                    <div className={styles.divider}>
                        OR
                    </div>

                    {/* ---------- SOCIAL LOGIN ---------- */}

                    <div className={styles.socialGrid}>

                        {socialProviders.map((provider) => (

                            <button
                                key={provider.id}
                                className={styles.socialButton}
                                type="button"
                            >

                                <strong>
                                    {provider.icon}
                                </strong>

                                <div
                                    style={{
                                        marginTop: 8,
                                        fontSize: ".9rem",
                                    }}
                                >
                                    {provider.name}
                                </div>

                            </button>

                        ))}

                    </div>

                    {/* ---------- FOOTER ---------- */}

                    <div className={styles.footer}>

                        Don't have an account?

                        {" "}

                        <a href="/register">
                            Create Account
                        </a>

                    </div>

                </section>

            </section>

        </main>

    );

};

export default Login;