export type EvolutionStatus =
    | "Planning"
    | "Training"
    | "Testing"
    | "Released"
    | "Deprecated";

export type BenchmarkType =
    | "Accuracy"
    | "Latency"
    | "Reasoning"
    | "Coding"
    | "Multimodal";

export interface ModelEvolution {

    id: string;

    version: string;

    title: string;

    description: string;

    releaseDate: string;

    status: EvolutionStatus;

    benchmark: BenchmarkType;

    score: number;

    improvement: number;

}

export interface RoadmapItem {

    id: string;

    milestone: string;

    targetDate: string;

    progress: number;

}

export interface EvolutionStatistics {

    totalVersions: number;

    activeVersions: number;

    experiments: number;

    benchmarks: number;

}

export interface EvolutionFilter {

    status: EvolutionStatus | "All";

    benchmark: BenchmarkType | "All";

}

export interface EvolutionProps {

    className?: string;

}