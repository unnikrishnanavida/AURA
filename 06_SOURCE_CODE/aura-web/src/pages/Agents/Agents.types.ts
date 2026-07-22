export type AgentStatus =
    | "online"
    | "offline"
    | "idle"
    | "busy"
    | "error";

export type AgentType =
    | "research"
    | "coding"
    | "vision"
    | "planning"
    | "memory"
    | "automation"
    | "security"
    | "cloud";

export interface Agent {
    id: string;
    name: string;
    description: string;
    type: AgentType;
    model: string;

    status: AgentStatus;

    cpuUsage: number;
    memoryUsage: number;
    tokenUsage: number;

    uptime: string;

    tasksCompleted: number;
    activeTasks: number;

    responseTime: number;

    lastSeen: string;
}

export interface AgentStats {
    total: number;
    online: number;
    busy: number;
    idle: number;
    offline: number;
    error: number;
}

export interface AgentFilter {
    search: string;
    status: AgentStatus | "all";
    type: AgentType | "all";
    model: string;
}

export interface AgentsProps {
    className?: string;
}