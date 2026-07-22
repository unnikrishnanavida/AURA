import { useState } from "react";
import {
    CheckCircle2,
    Eye,
    EyeOff,
    Lock,
    Mail,
    ShieldCheck,
    Sparkles,
    User,
    Building2,
} from "lucide-react";

import styles from "./Register.module.css";

import type {
    RegisterForm,
    SocialProvider,
} from "./Register.types";

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

const Register = () => {

    const [showPassword, setShowPassword] =
        useState(false);

    const [showConfirmPassword, setShowConfirmPassword] =
        useState(false);

    const [form, setForm] =
        useState<RegisterForm>({
            firstName: "",
            lastName: "",
            organization: "",
            email: "",
            password: "",
            confirmPassword: "",
            acceptTerms: false,
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
                        Build Intelligent AI Experiences
                    </h1>

                    <p className={styles.description}>
                        Join the AURA Enterprise AI Platform to
                        create, deploy and manage powerful AI
                        workflows securely at scale.
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
                            Multi-model AI Platform
                        </div>

                    </div>

                </section>

                {/* ================= REGISTER CARD ================= */}

                <section className={styles.card}>

                    <div>

                        <h2 className={styles.title}>
                            Create Account
                        </h2>

                        <p className={styles.subtitle}>
                            Get started with your AURA workspace.
                        </p>

                    </div>

                    {/* ---------- NAME ---------- */}

                    <div className={styles.grid}>

                        <div className={styles.formGroup}>

                            <label className={styles.label}>
                                First Name
                            </label>

                            <div className={styles.inputWrapper}>

                                <input
                                    className={styles.input}
                                    value={form.firstName}
                                    onChange={(e)=>
                                        setForm({
                                            ...form,
                                            firstName:e.target.value,
                                        })
                                    }
                                />

                                <button
                                    className={styles.iconButton}
                                    type="button"
                                >
                                    <User size={18}/>
                                </button>

                            </div>

                        </div>

                        <div className={styles.formGroup}>

                            <label className={styles.label}>
                                Last Name
                            </label>

                            <div className={styles.inputWrapper}>

                                <input
                                    className={styles.input}
                                    value={form.lastName}
                                    onChange={(e)=>
                                        setForm({
                                            ...form,
                                            lastName:e.target.value,
                                        })
                                    }
                                />

                                <button
                                    className={styles.iconButton}
                                    type="button"
                                >
                                    <User size={18}/>
                                </button>

                            </div>

                        </div>

                    </div>

                    {/* ---------- ORGANIZATION ---------- */}

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Organization
                        </label>

                        <div className={styles.inputWrapper}>

                            <input
                                className={styles.input}
                                value={form.organization}
                                onChange={(e)=>
                                    setForm({
                                        ...form,
                                        organization:e.target.value,
                                    })
                                }
                            />

                            <button
                                className={styles.iconButton}
                                type="button"
                            >
                                <Building2 size={18}/>
                            </button>

                        </div>

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
                                value={form.email}
                                placeholder="name@company.com"
                                onChange={(e)=>
                                    setForm({
                                        ...form,
                                        email:e.target.value,
                                    })
                                }
                            />

                            <button
                                className={styles.iconButton}
                                type="button"
                            >
                                <Mail size={18}/>
                            </button>

                        </div>

                    </div>

                    {/* ---------- PASSWORD ---------- */}

                    <div className={styles.grid}>

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
                                    value={form.password}
                                    onChange={(e)=>
                                        setForm({
                                            ...form,
                                            password:e.target.value,
                                        })
                                    }
                                />

                                <button
                                    type="button"
                                    className={styles.iconButton}
                                    onClick={()=>
                                        setShowPassword(
                                            !showPassword
                                        )
                                    }
                                >

                                    {showPassword
                                        ? <EyeOff size={18}/>
                                        : <Eye size={18}/>
                                    }

                                </button>

                            </div>

                        </div>

                        <div className={styles.formGroup}>

                            <label className={styles.label}>
                                Confirm Password
                            </label>

                            <div className={styles.inputWrapper}>

                                <input
                                    type={
                                        showConfirmPassword
                                            ? "text"
                                            : "password"
                                    }
                                    className={styles.input}
                                    value={form.confirmPassword}
                                    onChange={(e)=>
                                        setForm({
                                            ...form,
                                            confirmPassword:e.target.value,
                                        })
                                    }
                                />

                                <button
                                    type="button"
                                    className={styles.iconButton}
                                    onClick={()=>
                                        setShowConfirmPassword(
                                            !showConfirmPassword
                                        )
                                    }
                                >

                                    {showConfirmPassword
                                        ? <EyeOff size={18}/>
                                        : <Eye size={18}/>
                                    }

                                </button>

                            </div>

                        </div>

                    </div>
                                        {/* ---------- TERMS ---------- */}

                    <label className={styles.checkbox}>

                        <input
                            type="checkbox"
                            checked={form.acceptTerms}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    acceptTerms: e.target.checked,
                                })
                            }
                        />

                        <span>
                            I agree to the{" "}
                            <a
                                href="/terms"
                                className={styles.link}
                            >
                                Terms of Service
                            </a>{" "}
                            and{" "}
                            <a
                                href="/privacy"
                                className={styles.link}
                            >
                                Privacy Policy
                            </a>
                        </span>

                    </label>

                    {/* ---------- REGISTER BUTTON ---------- */}

                    <button
                        className={styles.registerButton}
                        type="button"
                    >
                        <Lock size={18} />

                        {" "}Create Account

                    </button>

                    {/* ---------- DIVIDER ---------- */}

                    <div className={styles.divider}>
                        OR
                    </div>

                    {/* ---------- SOCIAL SIGN UP ---------- */}

                    <div className={styles.socialGrid}>

                        {socialProviders.map((provider) => (

                            <button
                                key={provider.id}
                                type="button"
                                className={styles.socialButton}
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

                        Already have an account?

                        {" "}

                        <a href="/login">
                            Sign In
                        </a>

                    </div>

                </section>

            </section>

        </main>

    );

};

export default Register;