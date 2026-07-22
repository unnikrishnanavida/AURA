import { useNavigate } from "react-router-dom";
import {
    ArrowRight,
    Bot,
    BrainCircuit,
    Cpu,
    ShieldCheck,
    Sparkles,
    Zap,
} from "lucide-react";

import styles from "./Landing.module.css";

import type {
    FeatureCard,
    LandingProps,
    Statistic,
} from "./Landing.types";

const statistics: Statistic[] = [
    {
        label: "Enterprise Clients",
        value: "500+",
    },
    {
        label: "AI Models",
        value: "150+",
    },
    {
        label: "API Requests / Day",
        value: "20M+",
    },
    {
        label: "System Uptime",
        value: "99.99%",
    },
];

const features: FeatureCard[] = [
    {
        id: "agents",
        title: "Autonomous Agents",
        description:
            "Deploy intelligent AI agents capable of planning, reasoning and executing complex workflows.",
        icon: "Bot",
    },
    {
        id: "brain",
        title: "Unified AI Brain",
        description:
            "Persistent memory, long-term reasoning and contextual understanding across your organization.",
        icon: "Brain",
    },
    {
        id: "security",
        title: "Enterprise Security",
        description:
            "RBAC, encryption, auditing and enterprise-grade governance built into every workflow.",
        icon: "Shield",
    },
];

const Landing = ({
    className,
}: LandingProps) => {

    const navigate = useNavigate();

    return (

        <main
            className={`${styles.page} ${className ?? ""}`}
        >

            {/* ================= NAVBAR ================= */}

            <header className={styles.navbar}>

                <div className={styles.logo}>
                    AURA
                </div>

                <nav className={styles.navLinks}>

                    <a
                        href="#features"
                        className={styles.navLink}
                    >
                        Features
                    </a>

                    <a
                        href="#platform"
                        className={styles.navLink}
                    >
                        Platform
                    </a>

                    <a
                        href="#pricing"
                        className={styles.navLink}
                    >
                        Pricing
                    </a>

                    <a
                        href="#about"
                        className={styles.navLink}
                    >
                        About
                    </a>

                </nav>

                <div className={styles.actions}>

                    <button
                        className={styles.loginButton}
                        onClick={() =>
                            navigate("/login")
                        }
                    >
                        Login
                    </button>

                    <button
                        className={styles.getStartedButton}
                        onClick={() =>
                            navigate("/register")
                        }
                    >
                        Get Started
                    </button>

                </div>

            </header>

            {/* ================= HERO ================= */}

            <section className={styles.hero}>

                <div className={styles.heroContent}>

                    <div className={styles.badge}>

                        <Sparkles size={16} />

                        {" "}

                        Enterprise AI Platform

                    </div>

                    <h1 className={styles.title}>

                        Build the Future with

                        <br />

                        <span className={styles.highlight}>
                            Artificial Intelligence
                        </span>

                    </h1>

                    <p className={styles.description}>

                        AURA brings together autonomous AI
                        agents, enterprise security,
                        intelligent workflows, advanced
                        analytics, memory systems and
                        large language models into one
                        powerful enterprise platform.

                    </p>

                    <div className={styles.heroButtons}>

                        <button
                            className={styles.primaryButton}
                            onClick={() =>
                                navigate("/register")
                            }
                        >

                            Start Free

                            {" "}

                            <ArrowRight size={18} />

                        </button>

                        <button
                            className={styles.secondaryButton}
                            onClick={() =>
                                navigate("/laboratory")
                            }
                        >
                            Explore Platform
                        </button>

                    </div>

                </div>

                {/* ================= HERO VISUAL ================= */}

                <div className={styles.heroVisual}>

                    <div className={styles.visualCard}>

                        <h2
                            style={{
                                marginBottom: 30,
                                color: "#D4AF37",
                            }}
                        >
                            AI Command Center
                        </h2>

                        <div
                            style={{
                                display: "grid",
                                gap: 20,
                            }}
                        >

                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 14,
                                }}
                            >

                                <Bot size={28} />

                                <div>

                                    <strong>
                                        AI Agents
                                    </strong>

                                    <p>
                                        24 Active
                                    </p>

                                </div>

                            </div>

                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 14,
                                }}
                            >

                                <BrainCircuit size={28} />

                                <div>

                                    <strong>
                                        Neural Brain
                                    </strong>

                                    <p>
                                        Learning...
                                    </p>

                                </div>

                            </div>

                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 14,
                                }}
                            >

                                <Cpu size={28} />

                                <div>

                                    <strong>
                                        AI Models
                                    </strong>

                                    <p>
                                        156 Connected
                                    </p>

                                </div>

                            </div>

                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 14,
                                }}
                            >

                                <ShieldCheck size={28} />

                                <div>

                                    <strong>
                                        Security
                                    </strong>

                                    <p>
                                        Protected
                                    </p>

                                </div>

                            </div>

                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 14,
                                }}
                            >

                                <Zap size={28} />

                                <div>

                                    <strong>
                                        Workflows
                                    </strong>

                                    <p>
                                        Running Smoothly
                                    </p>

                                </div>

                            </div>

                        </div>

                    </div>

                </div>

            </section>

            {/* ================= STATISTICS ================= */}

            <section className={styles.stats}>

                {statistics.map((item) => (

                    <article
                        key={item.label}
                        className={styles.statCard}
                    >

                        <div className={styles.statValue}>
                            {item.value}
                        </div>

                        <div className={styles.statLabel}>
                            {item.label}
                        </div>

                    </article>

                ))}

            </section>
                        {/* ================= FEATURES ================= */}

            <section
                id="features"
                style={{
                    padding: "90px 6%",
                }}
            >

                <div
                    style={{
                        textAlign: "center",
                        marginBottom: 60,
                    }}
                >

                    <span className={styles.badge}>
                        Platform Features
                    </span>

                    <h2
                        style={{
                            fontSize: "3rem",
                            marginTop: 20,
                            marginBottom: 20,
                        }}
                    >
                        Everything You Need to Build
                        Enterprise AI
                    </h2>

                    <p
                        style={{
                            color: "#CBD5E1",
                            maxWidth: 720,
                            margin: "0 auto",
                            lineHeight: 1.8,
                        }}
                    >
                        From intelligent agents to secure
                        deployment, AURA provides every
                        component required for modern AI
                        applications.
                    </p>

                </div>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit,minmax(320px,1fr))",
                        gap: 30,
                    }}
                >

                    {features.map((feature) => (

                        <article
                            key={feature.id}
                            style={{
                                padding: 32,
                                borderRadius: 24,
                                background:
                                    "rgba(255,255,255,.05)",
                                border:
                                    "1px solid rgba(212,175,55,.15)",
                                backdropFilter: "blur(20px)",
                            }}
                        >

                            <div
                                style={{
                                    width: 60,
                                    height: 60,
                                    borderRadius: 16,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    marginBottom: 24,
                                    background:
                                        "rgba(212,175,55,.12)",
                                }}
                            >

                                {feature.icon === "Bot" && (
                                    <Bot size={30} />
                                )}

                                {feature.icon === "Brain" && (
                                    <BrainCircuit size={30} />
                                )}

                                {feature.icon === "Shield" && (
                                    <ShieldCheck size={30} />
                                )}

                            </div>

                            <h3
                                style={{
                                    fontSize: "1.4rem",
                                    marginBottom: 14,
                                }}
                            >
                                {feature.title}
                            </h3>

                            <p
                                style={{
                                    color: "#CBD5E1",
                                    lineHeight: 1.8,
                                }}
                            >
                                {feature.description}
                            </p>

                        </article>

                    ))}

                </div>

            </section>

            {/* ================= PLATFORM ================= */}

            <section
                id="platform"
                style={{
                    padding: "80px 6%",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 50,
                    alignItems: "center",
                }}
            >

                <div>

                    <span className={styles.badge}>
                        Why AURA
                    </span>

                    <h2
                        style={{
                            fontSize: "3rem",
                            margin: "25px 0",
                        }}
                    >
                        One Platform.
                        Unlimited Intelligence.
                    </h2>

                    <p
                        style={{
                            color: "#CBD5E1",
                            lineHeight: 1.9,
                            marginBottom: 30,
                        }}
                    >
                        Instead of combining dozens of AI
                        services, AURA provides one unified
                        ecosystem for intelligent automation,
                        memory management, model orchestration,
                        analytics and enterprise governance.
                    </p>

                    <div
                        style={{
                            display: "grid",
                            gap: 18,
                        }}
                    >

                        <div>
                            ✅ Autonomous AI Agents
                        </div>

                        <div>
                            ✅ Long-term Memory Engine
                        </div>

                        <div>
                            ✅ AI Laboratory
                        </div>

                        <div>
                            ✅ Enterprise Security
                        </div>

                        <div>
                            ✅ Multi-LLM Support
                        </div>

                        <div>
                            ✅ Cloud Native Deployment
                        </div>

                    </div>

                </div>

                <div>

                    <div
                        style={{
                            padding: 40,
                            borderRadius: 24,
                            background:
                                "rgba(255,255,255,.05)",
                            border:
                                "1px solid rgba(212,175,55,.15)",
                            backdropFilter: "blur(20px)",
                        }}
                    >

                        <h3
                            style={{
                                marginBottom: 24,
                                color: "#D4AF37",
                            }}
                        >
                            Enterprise Modules
                        </h3>

                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns:
                                    "repeat(2,1fr)",
                                gap: 20,
                            }}
                        >

                            {[
                                "Dashboard",
                                "Agents",
                                "Brain",
                                "Laboratory",
                                "Analytics",
                                "Automation",
                                "Knowledge",
                                "Security",
                                "Cloud OS",
                                "Evolution",
                                "Studio",
                                "Admin",
                            ].map((module) => (

                                <div
                                    key={module}
                                    style={{
                                        padding: 18,
                                        borderRadius: 16,
                                        textAlign: "center",
                                        background:
                                            "rgba(255,255,255,.04)",
                                    }}
                                >
                                    {module}
                                </div>

                            ))}

                        </div>

                    </div>

                </div>

            </section>
                        {/* ================= TESTIMONIALS ================= */}

            <section
                style={{
                    padding: "90px 6%",
                }}
            >

                <div
                    style={{
                        textAlign: "center",
                        marginBottom: 60,
                    }}
                >

                    <span className={styles.badge}>
                        Testimonials
                    </span>

                    <h2
                        style={{
                            fontSize: "3rem",
                            marginTop: 20,
                        }}
                    >
                        Trusted by Modern AI Teams
                    </h2>

                </div>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit,minmax(340px,1fr))",
                        gap: 30,
                    }}
                >

                    {[
                        {
                            name: "Sarah Johnson",
                            role: "CTO",
                            company: "Neural Labs",
                            quote:
                                "AURA unified our AI infrastructure into one intelligent platform.",
                        },
                        {
                            name: "Michael Chen",
                            role: "Engineering Manager",
                            company: "FutureStack",
                            quote:
                                "Deployment time dropped dramatically thanks to the built-in AI orchestration.",
                        },
                        {
                            name: "Ananya Rao",
                            role: "AI Architect",
                            company: "VisionAI",
                            quote:
                                "The Brain and Laboratory modules completely changed how our team experiments with AI.",
                        },
                    ].map((testimonial) => (

                        <article
                            key={testimonial.name}
                            style={{
                                padding: 32,
                                borderRadius: 24,
                                background:
                                    "rgba(255,255,255,.05)",
                                border:
                                    "1px solid rgba(212,175,55,.15)",
                                backdropFilter: "blur(20px)",
                            }}
                        >

                            <p
                                style={{
                                    color: "#CBD5E1",
                                    lineHeight: 1.9,
                                    marginBottom: 24,
                                }}
                            >
                                "{testimonial.quote}"
                            </p>

                            <strong>
                                {testimonial.name}
                            </strong>

                            <div
                                style={{
                                    color: "#94A3B8",
                                    marginTop: 6,
                                }}
                            >
                                {testimonial.role}
                            </div>

                            <div
                                style={{
                                    color: "#D4AF37",
                                }}
                            >
                                {testimonial.company}
                            </div>

                        </article>

                    ))}

                </div>

            </section>

            {/* ================= PRICING ================= */}

            <section
                id="pricing"
                style={{
                    padding: "90px 6%",
                }}
            >

                <div
                    style={{
                        textAlign: "center",
                        marginBottom: 60,
                    }}
                >

                    <span className={styles.badge}>
                        Pricing
                    </span>

                    <h2
                        style={{
                            fontSize: "3rem",
                            marginTop: 20,
                        }}
                    >
                        Plans for Every Team
                    </h2>

                </div>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit,minmax(320px,1fr))",
                        gap: 30,
                    }}
                >

                    {[
                        {
                            title: "Starter",
                            price: "$0",
                            features: [
                                "5 AI Agents",
                                "Basic Memory",
                                "Community Support",
                            ],
                        },
                        {
                            title: "Professional",
                            price: "$49",
                            features: [
                                "Unlimited Agents",
                                "AI Laboratory",
                                "Analytics",
                                "Priority Support",
                            ],
                        },
                        {
                            title: "Enterprise",
                            price: "Custom",
                            features: [
                                "Unlimited Everything",
                                "Admin Console",
                                "SSO",
                                "Dedicated Infrastructure",
                            ],
                        },
                    ].map((plan) => (

                        <article
                            key={plan.title}
                            style={{
                                padding: 36,
                                borderRadius: 24,
                                background:
                                    "rgba(255,255,255,.05)",
                                border:
                                    "1px solid rgba(212,175,55,.15)",
                                backdropFilter: "blur(20px)",
                            }}
                        >

                            <h3>{plan.title}</h3>

                            <h1
                                style={{
                                    color: "#D4AF37",
                                    margin: "18px 0",
                                }}
                            >
                                {plan.price}
                            </h1>

                            <div
                                style={{
                                    display: "grid",
                                    gap: 14,
                                    marginBottom: 30,
                                }}
                            >

                                {plan.features.map((feature) => (

                                    <div key={feature}>
                                        ✓ {feature}
                                    </div>

                                ))}

                            </div>

                            <button
                                className={styles.primaryButton}
                                onClick={() =>
                                    navigate("/register")
                                }
                            >
                                Choose Plan
                            </button>

                        </article>

                    ))}

                </div>

            </section>

            {/* ================= CTA ================= */}

            <section
                style={{
                    padding: "100px 6%",
                    textAlign: "center",
                }}
            >

                <div
                    style={{
                        maxWidth: 900,
                        margin: "0 auto",
                        padding: 60,
                        borderRadius: 28,
                        background:
                            "rgba(255,255,255,.05)",
                        border:
                            "1px solid rgba(212,175,55,.15)",
                        backdropFilter: "blur(20px)",
                    }}
                >

                    <h2
                        style={{
                            fontSize: "3rem",
                            marginBottom: 24,
                        }}
                    >
                        Ready to Build the Future with AI?
                    </h2>

                    <p
                        style={{
                            color: "#CBD5E1",
                            lineHeight: 1.8,
                            marginBottom: 40,
                        }}
                    >
                        Join thousands of organizations building
                        intelligent applications with AURA.
                    </p>

                    <button
                        className={styles.primaryButton}
                        onClick={() =>
                            navigate("/register")
                        }
                    >
                        Start Building Today
                    </button>

                </div>

            </section>

            {/* ================= FOOTER ================= */}

            <footer
                style={{
                    padding: "40px 6%",
                    borderTop:
                        "1px solid rgba(212,175,55,.12)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 20,
                }}
            >

                <div>

                    <div
                        className={styles.logo}
                    >
                        AURA
                    </div>

                    <p
                        style={{
                            color: "#94A3B8",
                            marginTop: 10,
                        }}
                    >
                        Enterprise AI Platform © 2026
                    </p>

                </div>

                <div
                    style={{
                        display: "flex",
                        gap: 24,
                        flexWrap: "wrap",
                    }}
                >

                    <a
                        className={styles.navLink}
                        href="#"
                    >
                        Privacy
                    </a>

                    <a
                        className={styles.navLink}
                        href="#"
                    >
                        Terms
                    </a>

                    <a
                        className={styles.navLink}
                        href="#"
                    >
                        Documentation
                    </a>

                    <a
                        className={styles.navLink}
                        href="#"
                    >
                        Contact
                    </a>

                </div>

            </footer>

        </main>

    );

};

export default Landing;