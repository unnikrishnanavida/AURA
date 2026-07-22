export type SecurityStatus =
    | "Healthy"
    | "Warning"
    | "Critical";

export type ThreatSeverity =
    | "Low"
    | "Medium"
    | "High"
    | "Critical";

export interface SecurityThreat {

    id: string;

    title: string;

    source: string;

    severity: ThreatSeverity;

    status: SecurityStatus;

    detectedAt: string;

    description: string;

}

export interface ActiveSession {

    id: string;

    user: string;

    ipAddress: string;

    device: string;

    location: string;

    lastActivity: string;

}

export interface SecurityStatistics {

    activeThreats: number;

    activeSessions: number;

    blockedAttempts: number;

    apiKeys: number;

}

export interface SecurityFilter {

    severity: ThreatSeverity | "All";

    status: SecurityStatus | "All";

}

export interface SecurityProps {

    className?: string;

}