import { useState } from "react";
import {
    BrainCircuit,
    FlaskConical,
    Play,
    SlidersHorizontal,
    Sparkles,
} from "lucide-react";

import styles from "./Laboratory.module.css";

import type {
    AIModel,
    Experiment,
    LaboratoryProps,
    Parameter,
} from "./Laboratory.types";

const models: AIModel[] = [
    {
        id: "gpt-5",
        name: "GPT-5",
        provider: "OpenAI",
        contextWindow: "256K",
    },
    {
        id: "claude-4",
        name: "Claude 4 Opus",
        provider: "Anthropic",
        contextWindow: "200K",
    },
    {
        id: "gemini-2.5",
        name: "Gemini 2.5 Pro",
        provider: "Google",
        contextWindow: "1M",
    },
    {
        id: "llama-4",
        name: "Llama 4 Maverick",
        provider: "Meta",
        contextWindow: "128K",
    },
    {
        id: "deepseek",
        name: "DeepSeek R1",
        provider: "DeepSeek",
        contextWindow: "128K",
    },
    {
        id: "mistral",
        name: "Mistral Large",
        provider: "Mistral AI",
        contextWindow: "128K",
    },
];

const experiments: Experiment[] = [
    {
        id: "1",
        name: "Reasoning Benchmark",
        model: "GPT-5",
        status: "Running",
        accuracy: 98,
    },
    {
        id: "2",
        name: "Agent Planning",
        model: "Claude 4",
        status: "Completed",
        accuracy: 97,
    },
    {
        id: "3",
        name: "Knowledge Retrieval",
        model: "Gemini",
        status: "Queued",
        accuracy: 94,
    },
];

const Laboratory = ({
    className,
}: LaboratoryProps) => {

    const [parameters, setParameters] =
        useState<Parameter[]>([
            {
                name: "Temperature",
                value: 0.7,
                min: 0,
                max: 2,
            },
            {
                name: "Top P",
                value: 0.95,
                min: 0,
                max: 1,
            },
            {
                name: "Max Tokens",
                value: 4096,
                min: 512,
                max: 32768,
            },
            {
                name: "Frequency Penalty",
                value: 0.2,
                min: 0,
                max: 2,
            },
        ]);

    return (

        <main
            className={`${styles.page} ${className ?? ""}`}
        >

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        AI Laboratory
                    </h1>

                    <p className={styles.subtitle}>
                        Experiment with models,
                        prompts, reasoning and
                        parameter tuning.
                    </p>

                </div>

                <button className={styles.runButton}>

                    <Play size={18} />

                    {" "}

                    Run Experiment

                </button>

            </header>

            {/* ================= MAIN GRID ================= */}

            <section className={styles.layout}>

                {/* ================= PARAMETERS ================= */}

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <SlidersHorizontal
                            size={20}
                        />

                        {" "}

                        Model Parameters

                    </h2>

                    <div className={styles.parameterGrid}>

                        {parameters.map(
                            (parameter, index) => (

                                <div
                                    key={parameter.name}
                                    className={
                                        styles.parameterRow
                                    }
                                >

                                    <strong>
                                        {parameter.name}
                                    </strong>

                                    <input
                                        type="range"
                                        className={
                                            styles.slider
                                        }
                                        min={parameter.min}
                                        max={parameter.max}
                                        step={0.01}
                                        value={
                                            parameter.value
                                        }
                                        onChange={(e) => {

                                            const updated =
                                                [...parameters];

                                            updated[index] = {
                                                ...parameter,
                                                value:
                                                    Number(
                                                        e
                                                            .target
                                                            .value
                                                    ),
                                            };

                                            setParameters(
                                                updated
                                            );

                                        }}
                                    />

                                    <div
                                        className={
                                            styles.value
                                        }
                                    >
                                        {parameter.value}
                                    </div>

                                </div>

                            )
                        )}

                    </div>

                </section>

                {/* ================= PLAYGROUND ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <FlaskConical
                            size={20}
                        />

                        {" "}

                        Prompt Playground

                    </h2>

                    <textarea
                        rows={14}
                        style={{
                            width: "100%",
                            resize: "none",
                            borderRadius: 16,
                            padding: 18,
                            background:
                                "rgba(255,255,255,.05)",
                            border:
                                "1px solid rgba(255,255,255,.08)",
                            color: "#FFF",
                            outline: "none",
                        }}
                        placeholder="Design a multi-agent AI workflow that analyzes customer feedback and produces executive insights..."
                    />

                </aside>

            </section>

            {/* ================= AVAILABLE MODELS ================= */}

            <section className={styles.panel}>

                <h2 className={styles.panelTitle}>

                    <BrainCircuit
                        size={20}
                    />

                    {" "}

                    Available AI Models

                </h2>

                <div className={styles.modelGrid}>

                    {models.map((model) => (

                        <article
                            key={model.id}
                            className={styles.modelCard}
                        >

                            <div
                                className={
                                    styles.modelName
                                }
                            >
                                {model.name}
                            </div>

                            <div
                                className={
                                    styles.provider
                                }
                            >
                                {model.provider}
                            </div>

                            <div
                                className={
                                    styles.context
                                }
                            >
                                Context:
                                {" "}
                                {model.contextWindow}
                            </div>

                        </article>

                    ))}

                </div>

            </section>
                        {/* ================= EXPERIMENT HISTORY ================= */}

            <section className={styles.layout}>

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>

                        <Sparkles size={20} />

                        {" "}

                        Experiment History

                    </h2>

                    <div className={styles.experimentList}>

                        {experiments.map((experiment) => (

                            <article
                                key={experiment.id}
                                className={styles.experimentCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                        marginBottom: 12,
                                    }}
                                >

                                    <strong>
                                        {experiment.name}
                                    </strong>

                                    <span
                                        className={styles.status}
                                    >
                                        {experiment.status}
                                    </span>

                                </div>

                                <div
                                    style={{
                                        color: "#94A3B8",
                                    }}
                                >
                                    Model:
                                    {" "}
                                    {experiment.model}
                                </div>

                                <div
                                    style={{
                                        marginTop: 10,
                                        color: "#D4AF37",
                                    }}
                                >
                                    Accuracy:
                                    {" "}
                                    {experiment.accuracy}%
                                </div>

                            </article>

                        ))}

                    </div>

                </section>

                {/* ================= LIVE METRICS ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Live Session Metrics
                    </h2>

                    <div className={styles.experimentList}>

                        {[
                            ["Input Tokens", "4,283"],
                            ["Output Tokens", "2,194"],
                            ["Latency", "412 ms"],
                            ["Estimated Cost", "$0.034"],
                            ["Context Usage", "61%"],
                            ["GPU Load", "73%"],
                            ["Inference Queue", "2"],
                        ].map(([label, value]) => (

                            <div
                                key={label}
                                className={styles.experimentCard}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                    }}
                                >

                                    <span>
                                        {label}
                                    </span>

                                    <strong
                                        style={{
                                            color: "#D4AF37",
                                        }}
                                    >
                                        {value}
                                    </strong>

                                </div>

                            </div>

                        ))}

                    </div>

                </aside>

            </section>

            {/* ================= MODEL BENCHMARK ================= */}

            <section className={styles.panel}>

                <h2 className={styles.panelTitle}>
                    Model Benchmark Comparison
                </h2>

                <div className={styles.modelGrid}>

                    {[
                        {
                            model: "GPT-5",
                            score: "98.8%",
                        },
                        {
                            model: "Claude 4",
                            score: "98.1%",
                        },
                        {
                            model: "Gemini 2.5",
                            score: "97.4%",
                        },
                        {
                            model: "DeepSeek R1",
                            score: "96.9%",
                        },
                        {
                            model: "Llama 4",
                            score: "95.8%",
                        },
                        {
                            model: "Mistral Large",
                            score: "95.3%",
                        },
                    ].map((item) => (

                        <article
                            key={item.model}
                            className={styles.modelCard}
                        >

                            <div className={styles.modelName}>
                                {item.model}
                            </div>

                            <div
                                style={{
                                    marginTop: 14,
                                    color: "#D4AF37",
                                    fontSize: "1.4rem",
                                    fontWeight: 700,
                                }}
                            >
                                {item.score}
                            </div>

                        </article>

                    ))}

                </div>

            </section>

            {/* ================= QUICK ACTIONS ================= */}

            <section className={styles.panel}>

                <h2 className={styles.panelTitle}>
                    Laboratory Actions
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
                        "Save Prompt",
                        "Duplicate Experiment",
                        "Export Results",
                        "Create Benchmark",
                        "Share Session",
                        "Deploy Model",
                        "Compare Responses",
                        "Open Playground",
                    ].map((action) => (

                        <button
                            key={action}
                            className={styles.runButton}
                        >
                            {action}
                        </button>

                    ))}

                </div>

            </section>

        </main>

    );

};

export default Laboratory;