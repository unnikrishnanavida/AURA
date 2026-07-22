import { useState } from "react";
import {
    Bot,
    Brain,
    GitBranch,
    Play,
    Settings,
    Sparkles,
    Wrench,
} from "lucide-react";

import styles from "./Studio.module.css";

import type {
    ModelConfiguration,
    Workflow,
    WorkflowNode,
} from "./Studio.types";

const workflows: Workflow[] = [
    {
        id: "WF-001",
        name: "Customer Support Agent",
        status: "Published",
        updatedAt: "10 mins ago",
        nodes: 7,
    },
    {
        id: "WF-002",
        name: "Research Pipeline",
        status: "Testing",
        updatedAt: "1 hour ago",
        nodes: 5,
    },
    {
        id: "WF-003",
        name: "Document Analyzer",
        status: "Draft",
        updatedAt: "Yesterday",
        nodes: 6,
    },
];

const workflowNodes: WorkflowNode[] = [
    {
        id: "1",
        title: "System Prompt",
        type: "Prompt",
        description:
            "Define assistant behavior and instructions.",
    },
    {
        id: "2",
        title: "GPT-5 Model",
        type: "Model",
        description:
            "Primary reasoning model.",
    },
    {
        id: "3",
        title: "Knowledge Search",
        type: "Tool",
        description:
            "Retrieve enterprise documents.",
    },
    {
        id: "4",
        title: "Confidence Check",
        type: "Condition",
        description:
            "Validate response confidence.",
    },
    {
        id: "5",
        title: "Final Response",
        type: "Output",
        description:
            "Return formatted answer.",
    },
];

const Studio = () => {

    const [selectedWorkflow, setSelectedWorkflow] =
        useState(workflows[0]);

    const [configuration, setConfiguration] =
        useState<ModelConfiguration>({
            provider: "OpenAI",
            model: "GPT-5",
            temperature: 0.7,
            maxTokens: 4096,
        });

    return (

        <main className={styles.page}>

            {/* ================= HEADER ================= */}

            <header className={styles.header}>

                <div>

                    <h1 className={styles.title}>
                        AI Studio
                    </h1>

                    <p className={styles.subtitle}>
                        Design, build and deploy enterprise AI workflows.
                    </p>

                </div>

                <button className={styles.primaryButton}>
                    Create Workflow
                </button>

            </header>

            {/* ================= MAIN GRID ================= */}

            <section className={styles.grid}>

                {/* ================= LEFT PANEL ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Workflow Library
                    </h2>

                    <div className={styles.toolbox}>

                        {workflows.map((workflow) => (

                            <div
                                key={workflow.id}
                                className={styles.tool}
                                onClick={() =>
                                    setSelectedWorkflow(workflow)
                                }
                            >

                                <strong>{workflow.name}</strong>

                                <div
                                    style={{
                                        marginTop: 8,
                                        fontSize: ".85rem",
                                        color: "#94A3B8",
                                    }}
                                >
                                    {workflow.status}
                                </div>

                                <div
                                    style={{
                                        fontSize: ".8rem",
                                        color: "#64748B",
                                    }}
                                >
                                    {workflow.nodes} Nodes
                                </div>

                            </div>

                        ))}

                    </div>

                    <h2 className={styles.panelTitle}>
                        Toolbox
                    </h2>

                    <div className={styles.toolbox}>

                        <div className={styles.tool}>
                            <Sparkles size={18} />
                            {" "}Prompt
                        </div>

                        <div className={styles.tool}>
                            <Brain size={18} />
                            {" "}Model
                        </div>

                        <div className={styles.tool}>
                            <Wrench size={18} />
                            {" "}Tool
                        </div>

                        <div className={styles.tool}>
                            <GitBranch size={18} />
                            {" "}Condition
                        </div>

                        <div className={styles.tool}>
                            <Bot size={18} />
                            {" "}Output
                        </div>

                    </div>

                </aside>

                {/* ================= WORKFLOW CANVAS ================= */}

                <section className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        {selectedWorkflow.name}
                    </h2>

                    <div className={styles.canvas}>

                        {workflowNodes.map((node) => (

                            <div
                                key={node.id}
                                className={styles.workflowNode}
                            >

                                <div className={styles.nodeTitle}>
                                    {node.title}
                                </div>

                                <div className={styles.nodeType}>
                                    {node.type}
                                </div>

                                <div
                                    className={styles.nodeDescription}
                                >
                                    {node.description}
                                </div>

                            </div>

                        ))}

                    </div>

                </section>

                {/* ================= CONFIGURATION ================= */}

                <aside className={styles.panel}>

                    <h2 className={styles.panelTitle}>
                        Model Configuration
                    </h2>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Provider
                        </label>

                        <input
                            className={styles.input}
                            value={configuration.provider}
                            onChange={(e) =>
                                setConfiguration({
                                    ...configuration,
                                    provider: e.target.value,
                                })
                            }
                        />

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Model
                        </label>

                        <input
                            className={styles.input}
                            value={configuration.model}
                            onChange={(e) =>
                                setConfiguration({
                                    ...configuration,
                                    model: e.target.value,
                                })
                            }
                        />

                    </div>
                                        <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Temperature
                        </label>

                        <input
                            type="range"
                            min={0}
                            max={1}
                            step={0.1}
                            className={styles.slider}
                            value={configuration.temperature}
                            onChange={(e) =>
                                setConfiguration({
                                    ...configuration,
                                    temperature: Number(e.target.value),
                                })
                            }
                        />

                        <span className={styles.label}>
                            {configuration.temperature.toFixed(1)}
                        </span>

                    </div>

                    <div className={styles.formGroup}>

                        <label className={styles.label}>
                            Max Tokens
                        </label>

                        <input
                            type="number"
                            className={styles.input}
                            value={configuration.maxTokens}
                            onChange={(e) =>
                                setConfiguration({
                                    ...configuration,
                                    maxTokens: Number(e.target.value),
                                })
                            }
                        />

                    </div>

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 12,
                            marginTop: 12,
                        }}
                    >

                        <button
                            className={styles.primaryButton}
                        >
                            <Play size={18} />

                            {" "}Run Workflow

                        </button>

                        <button
                            className={styles.primaryButton}
                        >
                            <Settings size={18} />

                            {" "}Save Configuration

                        </button>

                        <button
                            className={styles.deployButton}
                        >
                            Deploy Workflow
                        </button>

                    </div>

                    <div
                        style={{
                            marginTop: 20,
                            padding: 18,
                            borderRadius: 14,
                            background:
                                "rgba(255,255,255,.04)",
                        }}
                    >

                        <div
                            style={{
                                color: "#D4AF37",
                                fontWeight: 600,
                                marginBottom: 10,
                            }}
                        >
                            Current Workflow
                        </div>

                        <div
                            style={{
                                color: "#FFFFFF",
                                marginBottom: 8,
                            }}
                        >
                            {selectedWorkflow.name}
                        </div>

                        <div
                            style={{
                                color: "#94A3B8",
                                fontSize: ".9rem",
                            }}
                        >
                            Status: {selectedWorkflow.status}
                        </div>

                        <div
                            style={{
                                color: "#94A3B8",
                                fontSize: ".9rem",
                            }}
                        >
                            Nodes: {selectedWorkflow.nodes}
                        </div>

                        <div
                            style={{
                                color: "#94A3B8",
                                fontSize: ".9rem",
                            }}
                        >
                            Updated: {selectedWorkflow.updatedAt}
                        </div>

                    </div>

                </aside>

            </section>

        </main>

    );

};

export default Studio;