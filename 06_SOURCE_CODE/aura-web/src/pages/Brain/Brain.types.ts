export interface BrainProps {
    className?: string;
}

export interface MemoryNode {
    id: string;
    title: string;
    type: string;
    status: "active" | "processing" | "idle";
    connections: number;
}

export interface CognitiveMetric {
    label: string;
    value: string;
    change: string;
}

export interface AgentMemory {
    id: string;
    agent: string;
    context: string;
    tokens: number;
}