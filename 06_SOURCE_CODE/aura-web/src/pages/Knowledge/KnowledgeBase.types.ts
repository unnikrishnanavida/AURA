export type KnowledgeCategory =
    | "AI"
    | "Cloud"
    | "Security"
    | "Programming"
    | "Research"
    | "Documentation";

export type KnowledgeStatus =
    | "published"
    | "draft"
    | "archived";

export interface KnowledgeDocument {
    id: string;

    title: string;

    description: string;

    category: KnowledgeCategory;

    status: KnowledgeStatus;

    author: string;

    version: string;

    views: number;

    updatedAt: string;

    tags: string[];
}

export interface KnowledgeStatistics {

    total: number;

    published: number;

    drafts: number;

    archived: number;

}

export interface KnowledgeFilter {

    search: string;

    category: KnowledgeCategory | "All";

    status: KnowledgeStatus | "All";

}

export interface KnowledgeBaseProps {

    className?: string;

}