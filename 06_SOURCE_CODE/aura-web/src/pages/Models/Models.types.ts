export type ModelProvider =
    | "OpenAI"
    | "Anthropic"
    | "Google"
    | "Meta"
    | "Mistral"
    | "Ollama";

export type ModelStatus =
    | "running"
    | "stopped"
    | "downloading"
    | "error";

export type DeploymentType =
    | "Cloud"
    | "Local";

export interface AIModel {

    id: string;

    name: string;

    provider: ModelProvider;

    deployment: DeploymentType;

    status: ModelStatus;

    parameters: string;

    contextWindow: number;

    memoryUsage: string;

    tokenSpeed: string;

    latency: string;

    version: string;

}

export interface ModelStatistics {

    total:number;

    running:number;

    local:number;

    cloud:number;

}

export interface ModelFilter{

    search:string;

    provider:ModelProvider | "All";

    status:ModelStatus | "All";

}

export interface ModelsProps{

    className?:string;

}