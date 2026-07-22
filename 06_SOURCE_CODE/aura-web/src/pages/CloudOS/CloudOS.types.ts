export type CloudProvider =
    | "AWS"
    | "Azure"
    | "Google Cloud"
    | "Oracle Cloud"
    | "Private Cloud";

export type ServiceStatus =
    | "Healthy"
    | "Warning"
    | "Critical"
    | "Offline";

export interface CloudCluster {

    id: string;

    name: string;

    provider: CloudProvider;

    region: string;

    kubernetesVersion: string;

    nodes: number;

    cpuUsage: number;

    memoryUsage: number;

    storageUsage: number;

    status: ServiceStatus;

}

export interface InfrastructureSummary {

    clusters: number;

    nodes: number;

    runningPods: number;

    deployments: number;

}

export interface CloudFilter {

    provider: CloudProvider | "All";

    status: ServiceStatus | "All";

}

export interface CloudOSProps {

    className?: string;

}