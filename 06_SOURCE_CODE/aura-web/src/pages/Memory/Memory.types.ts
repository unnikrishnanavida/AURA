export type MemoryType =
    | "conversation"
    | "knowledge"
    | "document"
    | "code"
    | "preference";

export type MemoryStatus =
    | "active"
    | "archived"
    | "expired";

export interface MemoryItem {
    id: string;

    title: string;

    description: string;

    type: MemoryType;

    status: MemoryStatus;

    confidence: number;

    importance: number;

    createdAt: string;

    updatedAt: string;

    source: string;

    tags: string[];
}

export interface MemoryStatistics {

    total: number;

    active: number;

    archived: number;

    expired: number;

}

export interface MemoryFilter {

    search: string;

    type: MemoryType | "All";

    status: MemoryStatus | "All";

}

export interface MemoryProps {

    className?: string;

}