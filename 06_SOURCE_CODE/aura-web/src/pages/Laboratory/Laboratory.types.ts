export interface LaboratoryProps {
    className?: string;
}

export interface Experiment {
    id: string;
    name: string;
    model: string;
    status: "Running" | "Completed" | "Queued";
    accuracy: number;
}

export interface AIModel {
    id: string;
    name: string;
    provider: string;
    contextWindow: string;
}

export interface Parameter {
    name: string;
    value: number;
    min: number;
    max: number;
}