export type ResearchStatus =
    | "completed"
    | "running"
    | "queued"
    | "failed";

export type ResearchCategory =
    | "Artificial Intelligence"
    | "Machine Learning"
    | "Cyber Security"
    | "Cloud Computing"
    | "Software Engineering"
    | "Data Science";

export interface ResearchItem {
    id: string;
    title: string;
    description: string;
    category: ResearchCategory;
    status: ResearchStatus;

    source: string;
    author: string;

    confidence: number;
    progress: number;

    createdAt: string;
    updatedAt: string;
}

export interface ResearchStatistics {

    totalResearch:number;

    completed:number;

    running:number;

    queued:number;

    failed:number;

}

export interface ResearchFilter{

    search:string;

    category:ResearchCategory | "All";

    status:ResearchStatus | "All";

}

export interface ResearchProps{

    className?:string;

}