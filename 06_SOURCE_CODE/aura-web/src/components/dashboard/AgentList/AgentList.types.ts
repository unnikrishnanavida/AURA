import type { LucideIcon } from "lucide-react";

export type AgentStatus =
    | "online"
    | "busy"
    | "offline";

export interface Agent {
    id: string;
    name: string;
    description: string;
    icon: LucideIcon;
    status: AgentStatus;
    task: string;
    usage: number;
    lastActive: string;
}

export interface AgentListProps {
    agents: Agent[];
    onOpen?: (id: string) => void;
}