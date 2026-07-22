export type WorkflowStatus =
    | "Draft"
    | "Testing"
    | "Published";

export type NodeType =
    | "Prompt"
    | "Model"
    | "Tool"
    | "Condition"
    | "Output";

export interface WorkflowNode {

    id: string;

    title: string;

    type: NodeType;

    description: string;

}

export interface Workflow {

    id: string;

    name: string;

    status: WorkflowStatus;

    updatedAt: string;

    nodes: number;

}

export interface ModelConfiguration {

    provider: string;

    model: string;

    temperature: number;

    maxTokens: number;

}

export interface StudioProps {

    className?: string;

}