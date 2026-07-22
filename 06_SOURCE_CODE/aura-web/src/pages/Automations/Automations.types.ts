export type AutomationStatus =
    | "running"
    | "paused"
    | "stopped"
    | "failed";

export type AutomationTrigger =
    | "schedule"
    | "event"
    | "webhook"
    | "manual";

export interface AutomationWorkflow {

    id: string;

    name: string;

    description: string;

    trigger: AutomationTrigger;

    status: AutomationStatus;

    owner: string;

    executions: number;

    successRate: number;

    lastRun: string;

    nextRun: string;

}

export interface AutomationStatistics {

    total: number;

    running: number;

    paused: number;

    failed: number;

}

export interface AutomationFilter {

    search: string;

    trigger: AutomationTrigger | "All";

    status: AutomationStatus | "All";

}

export interface AutomationsProps {

    className?: string;

}